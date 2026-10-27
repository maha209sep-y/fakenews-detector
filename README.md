# TruthLens – AI-Based Fake News & Misinformation Detector

A full-stack project: paste a news text (or a link) and get a verdict (**Likely Fake / Likely Real / Uncertain**),
a credibility score, the reasons behind it, and a history/dashboard of all checks.

## Architecture

```
Browser (HTML/CSS/JS)  ──REST/JSON──►  FastAPI backend  ──►  SQLite (SQLAlchemy)
                                            │
                                            └──►  ML model (TF-IDF + Logistic Regression, scikit-learn)
                                                  + linguistic heuristics + explainability
```

| Layer | Tech | Files |
|-------|------|-------|
| Frontend | HTML, CSS, vanilla JS (canvas chart) | `frontend/` |
| Backend API | FastAPI, Pydantic | `backend/main.py`, `schemas.py`, `article_fetcher.py` |
| Database | SQLite via SQLAlchemy (switchable to PostgreSQL/MySQL) | `backend/database.py`, `models.py` |
| ML | scikit-learn pipeline | `backend/ml/` |
| Tests | pytest | `backend/test_api.py` |

## Quick start

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

python -m ml.train                # trains the model (auto-runs on first start too)
uvicorn main:app --reload
```

Open **http://127.0.0.1:8000** — API docs at **http://127.0.0.1:8000/docs**.

## IMPORTANT: use a real dataset for real accuracy

Out of the box the model trains on a tiny hand-written demo set (≈55 sentences) so the project runs immediately.
That is only for demonstration. For a proper project/report:

1. Download the **ISOT Fake News dataset** (`Fake.csv`, `True.csv`) from Kaggle
   ("Fake and real news dataset" by Clément Bisaillon), or the **LIAR** / **FakeNewsNet** datasets.
2. Put the files in the `data/` folder.
3. Run `python -m ml.train` again — it detects them automatically.
   (Any CSV with `text` (or `title`+`text`) and `label` (1=fake, 0=real) columns also works: `--data path.csv`.)

Note: ISOT news is from 2016-2017 and has stylistic quirks (e.g. real articles mention "Reuters"), so high
test accuracy (~98-99%) does **not** mean it will generalise to today's misinformation. Mention this limitation in your report.

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/analyze` | `{"text": "..."}` or `{"url": "https://..."}` → verdict, scores, reasons |
| GET | `/api/history?limit=&offset=&verdict=` | Past analyses |
| GET | `/api/analysis/{id}` | One analysis |
| DELETE | `/api/history/{id}` | Delete one |
| POST | `/api/feedback/{id}` | `{"label": "fake"\|"real"}` user correction |
| POST | `/api/retrain` | Retrain on dataset + user feedback |
| GET | `/api/stats` | Dashboard numbers |
| GET | `/api/health` | Health + model info |

## Database schema

Table `analyses`: `id, text, source_url, verdict, fake_probability, credibility_score, details_json, user_label, created_at`.

To use PostgreSQL: `export DATABASE_URL=postgresql://user:pass@localhost/fakenews` and `pip install psycopg2-binary`.

## How it works

1. **Preprocess** – lowercase, strip URLs.
2. **Features** – TF-IDF on unigrams + bigrams.
3. **Classifier** – Logistic Regression (fast, interpretable).
4. **Heuristics** – ALL-CAPS, `!!!`, clickbait phrases, "share this", missing source attribution nudge the score (max ±0.2).
5. **Explainability** – word contributions = TF-IDF value × model coefficient.
6. **Feedback loop** – user labels are stored and used by `/api/retrain`.

## Run tests

```bash
cd backend && pytest -q
```

## Ideas to extend (for a higher grade)

- Swap in a transformer (`distilbert-base-uncased` fine-tuned with Hugging Face) behind the same `predict()` function.
- Add fact-check lookup via the Google Fact Check Tools API.
- User accounts + JWT auth, rate limiting, Docker + docker-compose.
- Browser extension that calls `/api/analyze`.
- Multilingual support (Hindi etc.) with `xlm-roberta-base`.

## Limitations (be honest in your report)

The system detects *writing patterns* associated with misinformation; it does **not** verify facts against the real world.
Well-written false news can fool it and sensational true news can be flagged. It is a decision-support tool, not a judge.