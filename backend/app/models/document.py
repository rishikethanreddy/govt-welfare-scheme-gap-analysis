"""
Document model — the core entity of the system.

Each document represents a text record (question, complaint, query, etc.)
about a government welfare scheme, with full NLP annotations and provenance.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    # ── Original Content ──────────────────────────────────────────────────
    original_text = Column(Text, nullable=False, doc="Verbatim text as collected")
    normalized_text = Column(Text, nullable=True, doc="Cleaned/normalized version")
    language = Column(String(20), nullable=True, default="en", index=True)
    text_role = Column(
        String(50), nullable=True, default="query",
        doc="Role of this text: query, complaint, faq, news, discussion"
    )

    # ── NLP Annotations ───────────────────────────────────────────────────
    scheme_id = Column(Integer, ForeignKey("schemes.id"), nullable=True, index=True)
    scheme_name = Column(String(100), nullable=True, index=True, doc="Denormalized scheme name for fast queries")
    intent = Column(String(50), nullable=True, index=True)
    intent_confidence = Column(Float, nullable=True)
    awareness_gap = Column(String(10), nullable=True, index=True, doc="yes / no / unclear")
    gap_confidence = Column(Float, nullable=True)
    gap_type = Column(String(50), nullable=True, index=True)
    gap_type_confidence = Column(Float, nullable=True)

    # ── Geography ─────────────────────────────────────────────────────────
    state = Column(String(100), nullable=True, index=True)
    district = Column(String(100), nullable=True, index=True)
    state_id = Column(Integer, ForeignKey("geographic_entities.id"), nullable=True)
    district_id = Column(Integer, ForeignKey("geographic_entities.id"), nullable=True)

    # ── Provenance ────────────────────────────────────────────────────────
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True, index=True)
    source_name = Column(String(200), nullable=True, doc="Denormalized source name")
    source_type = Column(String(50), nullable=True)
    source_url = Column(String(2048), nullable=True)
    source_document_id = Column(String(200), nullable=True, doc="ID within the original source")
    source_date = Column(DateTime, nullable=True, doc="Publication/post date at source")
    scrape_run_id = Column(Integer, ForeignKey("source_runs.id"), nullable=True)

    # ── Dataset ───────────────────────────────────────────────────────────
    dataset_version_id = Column(Integer, ForeignKey("dataset_versions.id"), nullable=True, index=True)
    original_csv_id = Column(String(50), nullable=True, doc="ID from original CSV import")

    # ── Processing ────────────────────────────────────────────────────────
    processing_status = Column(
        String(20), nullable=False, default="pending", index=True,
        doc="pending / processing / completed / failed"
    )
    quality_score = Column(Float, nullable=True, doc="Composite quality score 0.0-1.0")
    confidence = Column(String(20), nullable=True, doc="Overall confidence: low / medium / high")
    notes = Column(Text, nullable=True)

    # ── Flags ─────────────────────────────────────────────────────────────
    is_synthetic = Column(Boolean, nullable=False, default=False)
    is_demo = Column(Boolean, nullable=False, default=False, doc="True for demo/sample records")
    is_duplicate = Column(Boolean, nullable=False, default=False)
    duplicate_group_id = Column(String(64), nullable=True, doc="Hash-based duplicate group ID")

    # ── PII ───────────────────────────────────────────────────────────────
    pii_detected = Column(Boolean, nullable=False, default=False)
    pii_redacted = Column(Boolean, nullable=False, default=False)

    # ── Embeddings ────────────────────────────────────────────────────────
    embedding_model = Column(String(100), nullable=True)
    # Embedding vectors stored as binary or in a separate table for large scale

    # ── Model Versions ────────────────────────────────────────────────────
    intent_model_version = Column(String(50), nullable=True)
    gap_model_version = Column(String(50), nullable=True)
    embedding_model_version = Column(String(50), nullable=True)
    scheme_detection_version = Column(String(50), nullable=True)

    # ── Split (for ML training) ───────────────────────────────────────────
    split = Column(String(10), nullable=True, index=True, doc="train / val / test")

    # ── Timestamps ────────────────────────────────────────────────────────
    collected_at = Column(DateTime, nullable=True, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # ── Relationships ─────────────────────────────────────────────────────
    scheme = relationship("Scheme", back_populates="documents", lazy="joined")
    source = relationship("Source", back_populates="documents", lazy="select")
    dataset_version = relationship("DatasetVersion", back_populates="documents", lazy="select")

    # ── Indexes ───────────────────────────────────────────────────────────
    __table_args__ = (
        Index("ix_documents_scheme_intent", "scheme_name", "intent"),
        Index("ix_documents_scheme_gap", "scheme_name", "awareness_gap"),
        Index("ix_documents_state_scheme", "state", "scheme_name"),
        Index("ix_documents_gap_type_state", "gap_type", "state"),
        Index("ix_documents_processing", "processing_status", "created_at"),
    )

    def __repr__(self):
        return f"<Document(id={self.id}, scheme={self.scheme_name}, intent={self.intent})>"
