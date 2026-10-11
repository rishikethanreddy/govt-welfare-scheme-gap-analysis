"""
Processing models — DatasetVersion and ProcessingJob.

DatasetVersion tracks each imported dataset with versioning.
ProcessingJob tracks background NLP/ingestion jobs.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Float
from sqlalchemy.orm import relationship
from backend.app.database import Base


class DatasetVersion(Base):
    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), nullable=False, unique=True, index=True, doc="e.g. v1.0, v2.0")
    name = Column(String(200), nullable=True, doc="Human-readable name")
    description = Column(Text, nullable=True)
    source_file = Column(String(500), nullable=True, doc="Original filename")
    source_type = Column(String(50), nullable=True, default="csv_upload", doc="csv_upload / api_import / scrape")

    # ── Metrics ───────────────────────────────────────────────────────────
    record_count = Column(Integer, nullable=False, default=0)
    valid_records = Column(Integer, nullable=False, default=0)
    duplicate_records = Column(Integer, nullable=False, default=0)
    rejected_records = Column(Integer, nullable=False, default=0)

    # ── Processing ────────────────────────────────────────────────────────
    processing_status = Column(
        String(20), nullable=False, default="imported",
        doc="imported / processing / processed / failed"
    )
    column_mapping = Column(Text, nullable=True, doc="JSON mapping of source→target columns")
    changes = Column(Text, nullable=True, doc="Description of what changed from previous version")

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ─────────────────────────────────────────────────────
    documents = relationship("Document", back_populates="dataset_version", lazy="select")

    def __repr__(self):
        return f"<DatasetVersion(id={self.id}, version={self.version}, records={self.record_count})>"


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(
        String(50), nullable=False, index=True,
        doc="nlp_pipeline / dataset_import / scrape / embedding / clustering / export / report"
    )
    status = Column(
        String(20), nullable=False, default="pending", index=True,
        doc="pending / running / completed / failed / cancelled"
    )

    # ── Progress ──────────────────────────────────────────────────────────
    total_items = Column(Integer, nullable=True)
    processed_items = Column(Integer, nullable=False, default=0)
    failed_items = Column(Integer, nullable=False, default=0)
    progress = Column(Float, nullable=False, default=0.0, doc="0.0 to 1.0")

    # ── Context ───────────────────────────────────────────────────────────
    params = Column(Text, nullable=True, doc="JSON parameters for this job")
    result = Column(Text, nullable=True, doc="JSON result summary")
    error_message = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ProcessingJob(id={self.id}, type={self.job_type}, status={self.status})>"
