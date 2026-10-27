"""SQLAlchemy table definitions (SQLAlchemy 2.0 typed style)."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Analysis(Base):
    """One row per analysed article / claim."""

    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    # Likely Fake / Likely Real / Uncertain
    verdict: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    fake_probability: Mapped[float] = mapped_column(Float, nullable=False)
    credibility_score: Mapped[int] = mapped_column(Integer, nullable=False)
    # signals + top terms stored as JSON text
    details_json: Mapped[str] = mapped_column(Text, nullable=False)
    # User feedback: "fake", "real" or NULL (used to retrain the model)
    user_label: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)