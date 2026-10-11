"""
Scheme schemas — scheme registry and intelligence responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SchemeResponse(BaseModel):
    id: int
    name: str
    short_name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    ministry: Optional[str] = None
    official_url: Optional[str] = None
    active: bool = True

    model_config = {"from_attributes": True}


class SchemeIntelligenceResponse(BaseModel):
    """Detailed scheme analysis with aggregated metrics."""
    scheme: SchemeResponse
    total_records: int = 0
    awareness_gap_signals: int = 0
    gap_rate: float = 0.0

    top_intents: list[dict] = Field(default_factory=list)
    top_gap_types: list[dict] = Field(default_factory=list)
    top_states: list[dict] = Field(default_factory=list)
    top_districts: list[dict] = Field(default_factory=list)
    recurring_questions: list[dict] = Field(default_factory=list)
    misconceptions: list[dict] = Field(default_factory=list)

    sources: list[str] = Field(default_factory=list)


class SchemeComparisonResponse(BaseModel):
    schemes: list[SchemeIntelligenceResponse] = []
