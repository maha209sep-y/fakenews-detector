"""Pydantic request / response schemas."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class AnalyzeRequest(BaseModel):
    text: Optional[str] = Field(None, description="Article text or claim to check")
    url: Optional[str] = Field(None, description="Or a link to a news article")

    @model_validator(mode="after")
    def need_one(self):
        if not (self.text and self.text.strip()) and not (self.url and self.url.strip()):
            raise ValueError("Provide either 'text' or 'url'.")
        if self.text and len(self.text) > 20000:
            raise ValueError("Text too long (max 20,000 characters).")
        return self


class Signal(BaseModel):
    name: str
    weight: float
    type: str


class Term(BaseModel):
    term: str
    score: float


class TopTerms(BaseModel):
    fake: list[Term]
    real: list[Term]


class AnalysisOut(BaseModel):
    id: int
    verdict: str
    fake_probability: float
    real_probability: float
    model_fake_probability: float
    credibility_score: int
    signals: list[Signal]
    top_terms: TopTerms
    source_url: Optional[str] = None
    excerpt: str
    user_label: Optional[str] = None
    created_at: datetime


class HistoryItem(BaseModel):
    id: int
    excerpt: str
    verdict: str
    credibility_score: int
    source_url: Optional[str] = None
    user_label: Optional[str] = None
    created_at: datetime


class FeedbackIn(BaseModel):
    label: Literal["fake", "real"]


class StatsOut(BaseModel):
    total: int
    fake: int
    real: int
    uncertain: int
    feedback_count: int
    avg_credibility: float
    last_7_days: list[dict]
    model: dict