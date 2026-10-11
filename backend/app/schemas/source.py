"""
Source schemas — data source registry and scrape run responses.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class SourceCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    url: Optional[str] = None
    source_type: str = "manual"
    organization: Optional[str] = None
    description: Optional[str] = None
    collection_method: str = "manual"
    schedule: str = "manual"
    crawl_delay: Optional[float] = None
    language: str = "en"


class SourceResponse(BaseModel):
    id: int
    name: str
    url: Optional[str] = None
    source_type: str
    organization: Optional[str] = None
    description: Optional[str] = None
    collection_method: Optional[str] = None
    policy_status: str = "manual_review"
    active: bool = True
    schedule: Optional[str] = None
    crawl_delay: Optional[float] = None

    # Operational
    last_run_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None
    total_records_collected: int = 0
    total_runs: int = 0
    health_score: Optional[float] = None

    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class SourceRunResponse(BaseModel):
    id: int
    source_id: int
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    urls_discovered: int = 0
    urls_attempted: int = 0
    successful: int = 0
    skipped: int = 0
    blocked: int = 0
    failed: int = 0
    records_extracted: int = 0
    records_accepted: int = 0
    duplicates_found: int = 0

    error_message: Optional[str] = None

    model_config = {"from_attributes": True}
