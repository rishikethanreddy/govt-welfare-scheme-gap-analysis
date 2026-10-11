"""
Common schemas — pagination, filtering, error responses.
"""

from datetime import datetime
from typing import Optional, Any, Generic, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Pagination ────────────────────────────────────────────────────────────

class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=50, ge=1, le=500, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class PaginatedResponse(BaseModel):
    items: list[Any] = []
    total: int = 0
    page: int = 1
    page_size: int = 50
    total_pages: int = 0


# ── Error Responses ───────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[str] = None
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Filters ───────────────────────────────────────────────────────────────

class DocumentFilter(BaseModel):
    """Global filter parameters shared across dashboard, analytics, and explorer."""
    scheme: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    intent: Optional[str] = None
    awareness_gap: Optional[str] = None
    gap_type: Optional[str] = None
    language: Optional[str] = None
    source: Optional[str] = None
    source_type: Optional[str] = None
    text_role: Optional[str] = None
    confidence: Optional[str] = None
    processing_status: Optional[str] = None
    split: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    is_synthetic: Optional[bool] = None
    is_demo: Optional[bool] = None


# ── Health ────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "healthy"
    environment: str = "development"
    version: str = "0.1.0"
    database: str = "connected"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SystemHealthResponse(BaseModel):
    api_status: str = "healthy"
    database_status: str = "unknown"
    database_type: str = "unknown"
    nlp_status: str = "not_initialized"
    scraper_status: str = "not_initialized"
    total_documents: int = 0
    total_sources: int = 0
    active_jobs: int = 0
    last_collection: Optional[datetime] = None
    failed_jobs_24h: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
