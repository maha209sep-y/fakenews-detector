"""
Train the fake-news classifier.

Usage (from the backend/ folder):
    python -m ml.train                    # uses data/*.csv if present, else seed data
    python -m ml.train --data ../data/news.csv

Supported CSV formats (put in ../data/):
  1. A single CSV with columns: text (or title+text) and label (1 = fake, 0 = real)
  2. Kaggle "Fake.csv" + "True.csv" (ISOT dataset) -- both files in ../data/
"""
import argparse
import json
import re
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from .seed_data import SEED_ROWS
from .text_utils import clean_text

BASE = Path(__file__).resolve().parent
MODEL_DIR = BASE / "artifacts"
MODEL_PATH = MODEL_DIR / "model.joblib"
METRICS_PATH = MODEL_DIR / "metrics.json"
DATA_DIR = BASE.parent.parent / "data"


def load_dataframe(data_path: str | None) -> tuple[pd.DataFrame, str]:
    # Explicit path
    if data_path:
        df = pd.read_csv(data_path)
        return _normalise(df), f"csv:{data_path}"

    # Kaggle ISOT style
    fake_csv, true_csv = DATA_DIR / "Fake.csv", DATA_DIR / "True.csv"
    if fake_csv.exists() and true_csv.exists():
        fake = pd.read_csv(fake_csv)
        real = pd.read_csv(true_csv)
        fake["label"], real["label"] = 1, 0
        df = pd.concat([fake, real], ignore_index=True)
        return _normalise(df), "kaggle-isot"

    # Any single CSV called news.csv
    news_csv = DATA_DIR / "news.csv"
    if news_csv.exists():
        return _normalise(pd.read_csv(news_csv)), "csv:news.csv"

    # Fall back to built-in seed data
    df = pd.DataFrame(SEED_ROWS, columns=["text", "label"])
    return df, "seed-demo-data"


def _normalise(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "title" in df.columns and "text" in df.columns:
        df["text"] = df["title"].fillna("") + ". " + df["text"].fillna("")
    elif "text" not in df.columns:
        raise ValueError("CSV needs a 'text' column (or 'title' + 'text').")
    if "label" not in df.columns:
        raise ValueError("CSV needs a 'label' column (1 = fake, 0 = real).")
    # Accept string labels too
    df["label"] = df["label"].map(
        lambda v: 1 if str(v).strip().lower() in {"1", "fake", "false", "unreliable"} else 0
    )
    df = df[["text", "label"]].dropna()
    df = df[df["text"].str.len() > 20]
    return df


def build_pipeline() -> Pipeline:
    return Pipeline(
        [
            (
                "tfidf",
                TfidfVectorizer(
                    preprocessor=clean_text,
                    ngram_range=(1, 2),
                    stop_words="english",
                    max_features=50000,
                    sublinear_tf=True,
                    min_df=1,
                ),
            ),
            ("clf", LogisticRegression(max_iter=1000, C=3.0, class_weight="balanced")),
        ]
    )


def train(data_path: str | None = None, extra_rows: list[tuple[str, int]] | None = None) -> dict:
    df, source = load_dataframe(data_path)
    if extra_rows:  # e.g. user feedback from the database
        extra = pd.DataFrame(extra_rows, columns=["text", "label"])
        df = pd.concat([df, extra], ignore_index=True)
        source += f"+feedback({len(extra)})"

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"], test_size=0.2, random_state=42, stratify=df["label"]
    )
    pipe = build_pipeline()
    pipe.fit(X_train, y_train)
    pred = pipe.predict(X_test)

    metrics = {
        "data_source": source,
        "n_samples": int(len(df)),
        "n_test": int(len(y_test)),
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "f1": round(float(f1_score(y_test, pred)), 4),
        "report": classification_report(y_test, pred, target_names=["real", "fake"], output_dict=True),
    }

    # Refit on everything for the final model
    pipe.fit(df["text"], df["label"])
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODEL_PATH)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=None, help="Path to a CSV with text,label columns")
    args = ap.parse_args()
    m = train(args.data)
    print(f"Trained on {m['n_samples']} samples from {m['data_source']}")
    print(f"Accuracy: {m['accuracy']}  F1: {m['f1']}")
    print(f"Model saved to {MODEL_PATH}")
    if m["data_source"] == "seed-demo-data":
        print("NOTE: this used the tiny demo dataset. See README to train on a real dataset.")