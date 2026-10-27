"""
Prediction + explainability.

Combines:
  * the trained TF-IDF + Logistic Regression model (main signal)
  * simple linguistic heuristics (clickbait, ALL CAPS, '!!!', no attribution ...)
  * top words that pushed the model towards fake / real (explainability)
"""
import json
import re
from functools import lru_cache

import joblib
import numpy as np

from .text_utils import clean_text
from .train import METRICS_PATH, MODEL_PATH, train

SENSATIONAL = {
    "shocking", "breaking", "urgent", "secret", "exposed", "miracle", "unbelievable",
    "you won't believe", "hate", "banned", "leaked", "cover up", "wake up", "share this",
    "they don't want you", "doctors hate", "100% proven", "deep state", "hoax",
}
ATTRIBUTION = re.compile(
    r"\b(according to|said|told reporters|announced|stated|reported|spokesperson|official|ministry|study|published|journal|press conference)\b",
    re.I,
)


@lru_cache(maxsize=1)
def _load():
    if not MODEL_PATH.exists():
        train()  # auto-train on first run so the API never starts without a model
    return joblib.load(MODEL_PATH)


def reload_model():
    _load.cache_clear()
    return _load()


def model_metrics() -> dict:
    if METRICS_PATH.exists():
        m = json.loads(METRICS_PATH.read_text())
        m.pop("report", None)
        return m
    return {}


def heuristic_signals(text: str) -> list[dict]:
    """Human-readable red / green flags. Weight > 0 pushes towards fake."""
    signals = []
    words = text.split()
    n_words = max(len(words), 1)
    lower = text.lower()

    caps_words = [w for w in words if len(w) > 3 and w.isupper() and w.isalpha()]
    if len(caps_words) / n_words > 0.08 or len(caps_words) >= 3:
        signals.append({"name": "Excessive ALL-CAPS words", "weight": 0.12, "type": "red"})

    if re.search(r"[!?]{2,}", text) or text.count("!") >= 3:
        signals.append({"name": "Repeated exclamation / question marks", "weight": 0.10, "type": "red"})

    hits = [s for s in SENSATIONAL if s in lower]
    if hits:
        signals.append(
            {"name": "Sensational / clickbait phrasing: " + ", ".join(sorted(hits)[:4]),
             "weight": min(0.08 * len(hits), 0.25), "type": "red"}
        )

    if re.search(r"(share (this|it)|forward(ed)? (this|as received)|send (this )?to \d+)", lower):
        signals.append({"name": "Asks you to share / forward urgently", "weight": 0.15, "type": "red"})

    if ATTRIBUTION.search(text):
        signals.append({"name": "Attributes claims to sources or officials", "weight": -0.10, "type": "green"})
    elif n_words > 25:
        signals.append({"name": "No clear source attribution", "weight": 0.06, "type": "red"})

    if re.search(r"\b\d+(\.\d+)?\s?(%|percent|million|billion|crore|lakh)\b", lower):
        signals.append({"name": "Contains specific, checkable figures", "weight": -0.05, "type": "green"})

    if n_words < 8:
        signals.append({"name": "Very short text - low confidence", "weight": 0.0, "type": "info"})
    return signals


def top_terms(pipe, text: str, k: int = 6) -> dict:
    """Words in the input that contributed most to fake / real (via LR coefficients)."""
    tfidf, clf = pipe.named_steps["tfidf"], pipe.named_steps["clf"]
    vec = tfidf.transform([text])
    names = np.array(tfidf.get_feature_names_out())
    idx = vec.nonzero()[1]
    if len(idx) == 0:
        return {"fake": [], "real": []}
    contrib = vec[0, idx].toarray().ravel() * clf.coef_[0][idx]
    order = np.argsort(contrib)
    fake_idx = [i for i in order[::-1] if contrib[i] > 0][:k]
    real_idx = [i for i in order if contrib[i] < 0][:k]
    return {
        "fake": [{"term": names[idx[i]], "score": round(float(contrib[i]), 4)} for i in fake_idx],
        "real": [{"term": names[idx[i]], "score": round(float(-contrib[i]), 4)} for i in real_idx],
    }


def predict(text: str) -> dict:
    pipe = _load()
    cleaned = clean_text(text)
    p_fake_model = float(pipe.predict_proba([cleaned])[0][1])

    signals = heuristic_signals(text)
    adj = sum(s["weight"] for s in signals)
    # Blend: model dominates, heuristics nudge (max +/- 0.2)
    p_fake = float(np.clip(p_fake_model + np.clip(adj, -0.2, 0.2), 0.0, 1.0))

    if p_fake >= 0.65:
        verdict = "Likely Fake"
    elif p_fake <= 0.35:
        verdict = "Likely Real"
    else:
        verdict = "Uncertain"

    return {
        "verdict": verdict,
        "fake_probability": round(p_fake, 4),
        "real_probability": round(1 - p_fake, 4),
        "model_fake_probability": round(p_fake_model, 4),
        "credibility_score": int(round((1 - p_fake) * 100)),
        "signals": signals,
        "top_terms": top_terms(pipe, cleaned),
    }