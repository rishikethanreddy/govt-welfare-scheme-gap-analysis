"""
Analytics schemas — geographic, intent, and gap analytics responses.
"""

from typing import Optional
from pydantic import BaseModel, Field


class GeographicMetric(BaseModel):
    state: str
    total_records: int = 0
    gap_signals: int = 0
    gap_rate: float = 0.0
    top_scheme: Optional[str] = None
    top_intent: Optional[str] = None
    top_gap_type: Optional[str] = None


class DistrictMetric(BaseModel):
    state: str
    district: str
    total_records: int = 0
    gap_signals: int = 0
    gap_rate: float = 0.0


class StateDetailResponse(BaseModel):
    state: str
    total_records: int = 0
    gap_signals: int = 0
    gap_rate: float = 0.0
    districts: list[DistrictMetric] = Field(default_factory=list)
    scheme_distribution: list[dict] = Field(default_factory=list)
    intent_distribution: list[dict] = Field(default_factory=list)
    gap_type_distribution: list[dict] = Field(default_factory=list)


class GeographicResponse(BaseModel):
    states: list[GeographicMetric] = []
    total_states: int = 0
    total_districts: int = 0


class ClusterResponse(BaseModel):
    id: int
    cluster_label: int
    name: Optional[str] = None
    size: int = 0
    representative_text: Optional[str] = None
    dominant_scheme: Optional[str] = None
    dominant_intent: Optional[str] = None
    dominant_gap_type: Optional[str] = None
    algorithm: Optional[str] = None

    model_config = {"from_attributes": True}


class ModelVersionResponse(BaseModel):
    id: int
    model_name: str
    model_type: str
    version: str
    description: Optional[str] = None
    status: str = "trained"
    is_active: bool = False

    # Metrics — null until real evaluation
    accuracy: Optional[float] = None
    precision_score: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    training_samples: Optional[int] = None
    validation_samples: Optional[int] = None

    model_config = {"from_attributes": True}


class FilterOptionsResponse(BaseModel):
    """Available filter values for the frontend to populate dropdowns."""
    schemes: list[str] = Field(default_factory=list)
    states: list[str] = Field(default_factory=list)
    districts: list[str] = Field(default_factory=list)
    intents: list[str] = Field(default_factory=list)
    gap_types: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)
