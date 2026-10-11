"""
Source and SourceRun models — data source registry and collection tracking.

Every data source (government portal, open-data API, RSS feed, uploaded CSV, etc.)
is registered here with its collection policy and operational status.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    url = Column(String(2048), nullable=True)
    source_type = Column(
        String(50), nullable=False, default="manual", index=True,
        doc="government_portal / open_data / api / rss / news / csv_upload / web / other"
    )
    organization = Column(String(200), nullable=True)
    country = Column(String(50), nullable=True, default="India")
    language = Column(String(50), nullable=True, default="en")
    description = Column(Text, nullable=True)

    # ── Collection Policy ─────────────────────────────────────────────────
    collection_method = Column(
        String(50), nullable=True, default="manual",
        doc="api / open_data / rss / html_scrape / json_download / manual"
    )
    policy_status = Column(
        String(30), nullable=False, default="manual_review",
        doc="allowed / allowed_with_limits / api_preferred / manual_review / blocked / unsupported"
    )
    robots_checked = Column(Boolean, nullable=False, default=False)
    terms_checked = Column(Boolean, nullable=False, default=False)
    api_available = Column(Boolean, nullable=False, default=False)
    auth_required = Column(Boolean, nullable=False, default=False)
    crawl_delay = Column(Float, nullable=True, doc="Seconds between requests")
    rate_limit = Column(String(100), nullable=True, doc="e.g., 100/hour")
    content_type = Column(String(100), nullable=True, doc="Expected content type (html, json, csv)")

    # ── Operational ───────────────────────────────────────────────────────
    active = Column(Boolean, nullable=False, default=True, index=True)
    schedule = Column(
        String(20), nullable=True, default="manual",
        doc="manual / daily / weekly / monthly"
    )
    last_run_at = Column(DateTime, nullable=True)
    last_success_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    total_records_collected = Column(Integer, nullable=False, default=0)
    total_runs = Column(Integer, nullable=False, default=0)

    # ── Health ────────────────────────────────────────────────────────────
    health_score = Column(Float, nullable=True, doc="Operational health 0.0-1.0 based on recent runs")

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ─────────────────────────────────────────────────────
    documents = relationship("Document", back_populates="source", lazy="select")
    runs = relationship("SourceRun", back_populates="source", lazy="select", order_by="SourceRun.started_at.desc()")

    def __repr__(self):
        return f"<Source(id={self.id}, name={self.name}, type={self.source_type})>"


class SourceRun(Base):
    __tablename__ = "source_runs"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)

    # ── Run Status ────────────────────────────────────────────────────────
    status = Column(
        String(20), nullable=False, default="running",
        doc="running / completed / failed / cancelled"
    )
    started_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    finished_at = Column(DateTime, nullable=True)

    # ── Metrics ───────────────────────────────────────────────────────────
    urls_discovered = Column(Integer, nullable=False, default=0)
    urls_attempted = Column(Integer, nullable=False, default=0)
    successful = Column(Integer, nullable=False, default=0)
    skipped = Column(Integer, nullable=False, default=0)
    blocked = Column(Integer, nullable=False, default=0)
    failed = Column(Integer, nullable=False, default=0)
    records_extracted = Column(Integer, nullable=False, default=0)
    records_accepted = Column(Integer, nullable=False, default=0)
    records_rejected = Column(Integer, nullable=False, default=0)
    duplicates_found = Column(Integer, nullable=False, default=0)

    # ── Error ─────────────────────────────────────────────────────────────
    error_message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────
    source = relationship("Source", back_populates="runs")

    __table_args__ = (
        Index("ix_source_runs_source_status", "source_id", "status"),
    )

    def __repr__(self):
        return f"<SourceRun(id={self.id}, source_id={self.source_id}, status={self.status})>"
