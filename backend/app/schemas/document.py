"""
Document schemas — request/response models for the document API.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    original_text: str
    scheme_name: Optional[str] = None
    intent: Optional[str] = None
    awareness_gap: Optional[str] = None
    gap_type: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    language: Optional[str] = "en"
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    original_text: str
    normalized_text: Optional[str] = None
    language: Optional[str] = None
    text_role: Optional[str] = None

    # NLP annotations
    scheme_name: Optional[str] = None
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    awareness_gap: Optional[str] = None
    gap_confidence: Optional[float] = None
    gap_type: Optional[str] = None
    gap_type_confidence: Optional[float] = None

    # Geography
    state: Optional[str] = None
    district: Optional[str] = None

    # Provenance
    source_name: Optional[str] = None
    source_type: Optional[str] = None
    source_url: Optional[str] = None
    source_document_id: Optional[str] = None

    # Metadata
    confidence: Optional[str] = None
    notes: Optional[str] = None
    is_synthetic: bool = False
    is_demo: bool = False
    is_duplicate: bool = False
    processing_status: str = "pending"
    quality_score: Optional[float] = None
    split: Optional[str] = None

    # Model versions
    intent_model_version: Optional[str] = None
    gap_model_version: Optional[str] = None
    embedding_model_version: Optional[str] = None

    # Timestamps
    collected_at: Optional[datetime] = None
    processed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse] = []
    total: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0


class DocumentDetailResponse(DocumentResponse):
    """Extended document response with related questions and cluster info."""
    related_questions: list[dict] = Field(default_factory=list)
    cluster_name: Optional[str] = None
    cluster_id: Optional[int] = None


# ── Text Analysis ─────────────────────────────────────────────────────────

class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=5000, description="Text to analyze")


class AnalyzeTextResponse(BaseModel):
    text: str
    normalized_text: str

    # Scheme
    scheme: Optional[str] = None
    scheme_confidence: Optional[float] = None
    scheme_matched_entities: list[str] = Field(default_factory=list)

    # Intent
    intent: Optional[str] = None
    intent_confidence: Optional[float] = None

    # Awareness Gap
    awareness_gap: Optional[str] = None
    gap_confidence: Optional[float] = None
    gap_type: Optional[str] = None
    gap_type_confidence: Optional[float] = None

    # Supporting signals
    supporting_signals: list[dict] = Field(default_factory=list)

    # Language
    language: Optional[str] = None

    # Geography
    geography: Optional[str] = None

    # Related
    related_questions: list[dict] = Field(default_factory=list)
    cluster: Optional[str] = None

    # Model info
    model_versions: dict = Field(default_factory=dict)


# ── Dataset Upload ────────────────────────────────────────────────────────

class DatasetUploadResponse(BaseModel):
    dataset_version_id: int
    version: str
    total_records: int
    valid_records: int
    duplicate_records: int
    rejected_records: int
    column_mapping: Optional[dict] = None
    processing_status: str

class DatasetVersionResponse(BaseModel):
    id: int
    version: str
    name: Optional[str] = None
    description: Optional[str] = None
    source_file: Optional[str] = None
    record_count: int = 0
    valid_records: int = 0
    duplicate_records: int = 0
    processing_status: str = "imported"
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
