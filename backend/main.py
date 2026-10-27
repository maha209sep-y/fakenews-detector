"""
FastAPI application: REST API + serves the frontend.

Run (from backend/):
    uvicorn main:app --reload
Open http://127.0.0.1:8000
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
import schemas
from article_fetcher import FetchError, fetch_article
from database import Base, engine, get_db
from ml import predictor
from ml.train import train

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Fake News & Misinformation Detector", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten for production
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


def _excerpt(text: str, n: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"


def _to_out(row: models.Analysis) -> schemas.AnalysisOut:
    d = json.loads(row.details_json)
    return schemas.AnalysisOut(
        id=row.id,
        verdict=row.verdict,
        fake_probability=row.fake_probability,
        real_probability=round(1 - row.fake_probability, 4),
        model_fake_probability=d["model_fake_probability"],
        credibility_score=row.credibility_score,
        signals=d["signals"],
        top_terms=d["top_terms"],
        source_url=row.source_url,
        excerpt=_excerpt(row.text),
        user_label=row.user_label,
        created_at=row.created_at,
    )


# ---------------------------------------------------------------- API

@app.get("/api/health")
def health():
    return {"status": "ok", "model": predictor.model_metrics()}


@app.post("/api/analyze", response_model=schemas.AnalysisOut)
def analyze(req: schemas.AnalyzeRequest, db: Session = Depends(get_db)):
    source_url = None
    text = (req.text or "").strip()
    if not text:
        try:
            text = fetch_article(req.url)
            source_url = req.url.strip()
        except FetchError as e:
            raise HTTPException(status_code=422, detail=str(e))
    if len(text) < 15:
        raise HTTPException(status_code=422, detail="Text is too short to analyse (min 15 characters).")

    result = predictor.predict(text)
    row = models.Analysis(
        text=text,
        source_url=source_url,
        verdict=result["verdict"],
        fake_probability=result["fake_probability"],
        credibility_score=result["credibility_score"],
        details_json=json.dumps(
            {
                "signals": result["signals"],
                "top_terms": result["top_terms"],
                "model_fake_probability": result["model_fake_probability"],
            }
        ),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _to_out(row)


@app.get("/api/history", response_model=list[schemas.HistoryItem])
def history(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    verdict: str | None = Query(None, description="Filter: Likely Fake / Likely Real / Uncertain"),
    db: Session = Depends(get_db),
):
    q = db.query(models.Analysis)
    if verdict:
        q = q.filter(models.Analysis.verdict == verdict)
    rows = q.order_by(models.Analysis.created_at.desc()).offset(offset).limit(limit).all()
    return [
        schemas.HistoryItem(
            id=r.id, excerpt=_excerpt(r.text, 120), verdict=r.verdict,
            credibility_score=r.credibility_score, source_url=r.source_url,
            user_label=r.user_label, created_at=r.created_at,
        )
        for r in rows
    ]


@app.get("/api/analysis/{analysis_id}", response_model=schemas.AnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Analysis, analysis_id)
    if not row:
        raise HTTPException(404, "Analysis not found")
    return _to_out(row)


@app.delete("/api/history/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    row = db.get(models.Analysis, analysis_id)
    if not row:
        raise HTTPException(404, "Analysis not found")
    db.delete(row)
    db.commit()


@app.post("/api/feedback/{analysis_id}", response_model=schemas.AnalysisOut)
def feedback(analysis_id: int, body: schemas.FeedbackIn, db: Session = Depends(get_db)):
    """User tells us the true label; stored and used by /api/retrain."""
    row = db.get(models.Analysis, analysis_id)
    if not row:
        raise HTTPException(404, "Analysis not found")
    row.user_label = body.label
    db.commit()
    db.refresh(row)
    return _to_out(row)


@app.post("/api/retrain")
def retrain(db: Session = Depends(get_db)):
    """Retrain the model on base dataset + user-labelled feedback."""
    rows = db.query(models.Analysis).filter(models.Analysis.user_label.isnot(None)).all()
    extra = [(r.text, 1 if r.user_label == "fake" else 0) for r in rows]
    metrics = train(extra_rows=extra)
    predictor.reload_model()
    metrics.pop("report", None)
    return {"message": "Model retrained", "metrics": metrics}


@app.get("/api/stats", response_model=schemas.StatsOut)
def stats(db: Session = Depends(get_db)):
    A = models.Analysis
    total = db.query(func.count(A.id)).scalar() or 0
    by_verdict = dict(db.query(A.verdict, func.count(A.id)).group_by(A.verdict).all())
    feedback_count = db.query(func.count(A.id)).filter(A.user_label.isnot(None)).scalar() or 0
    avg = db.query(func.avg(A.credibility_score)).scalar() or 0

    since = datetime.now(timezone.utc) - timedelta(days=6)
    recent = db.query(A.created_at, A.verdict).filter(A.created_at >= since.replace(hour=0, minute=0, second=0)).all()
    days = {}
    for i in range(7):
        d = (since + timedelta(days=i)).date().isoformat()
        days[d] = {"date": d, "fake": 0, "real": 0, "uncertain": 0}
    for created, verdict in recent:
        key = created.date().isoformat()
        if key in days:
            days[key]["fake" if verdict == "Likely Fake" else "real" if verdict == "Likely Real" else "uncertain"] += 1

    return schemas.StatsOut(
        total=total,
        fake=by_verdict.get("Likely Fake", 0),
        real=by_verdict.get("Likely Real", 0),
        uncertain=by_verdict.get("Uncertain", 0),
        feedback_count=feedback_count,
        avg_credibility=round(float(avg), 1),
        last_7_days=list(days.values()),
        model=predictor.model_metrics(),
    )


# ---------------------------------------------------------------- Frontend

app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")