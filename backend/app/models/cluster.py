"""
Cluster models — semantic clusters of documents.

Clusters group semantically similar documents discovered through
embedding-based clustering (HDBSCAN, K-Means, etc.).
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime,
    ForeignKey, Index
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class Cluster(Base):
    __tablename__ = "clusters"

    id = Column(Integer, primary_key=True, index=True)
    cluster_label = Column(Integer, nullable=False, doc="Numeric cluster ID from algorithm")
    name = Column(String(200), nullable=True, doc="Auto-generated or human-assigned cluster name")
    description = Column(Text, nullable=True)

    # ── Cluster Metadata ──────────────────────────────────────────────────
    size = Column(Integer, nullable=False, default=0)
    representative_text = Column(Text, nullable=True, doc="Most central document text")
    representative_texts = Column(Text, nullable=True, doc="JSON array of top-N representative texts")

    # ── Dominant Attributes ───────────────────────────────────────────────
    dominant_scheme = Column(String(100), nullable=True)
    dominant_intent = Column(String(50), nullable=True)
    dominant_gap_type = Column(String(50), nullable=True)
    dominant_state = Column(String(100), nullable=True)

    # ── Algorithm ─────────────────────────────────────────────────────────
    algorithm = Column(String(50), nullable=True, doc="hdbscan / kmeans / dbscan / agglomerative")
    model_version = Column(String(50), nullable=True)
    embedding_model = Column(String(100), nullable=True)
    run_id = Column(String(50), nullable=True, doc="Identifier for this clustering run")

    # ── Timestamps ────────────────────────────────────────────────────────
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # ── Relationships ─────────────────────────────────────────────────────
    document_clusters = relationship("DocumentCluster", back_populates="cluster", lazy="select")

    def __repr__(self):
        return f"<Cluster(id={self.id}, name={self.name}, size={self.size})>"


class DocumentCluster(Base):
    """Association table linking documents to clusters with similarity scores."""
    __tablename__ = "document_clusters"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False, index=True)
    cluster_id = Column(Integer, ForeignKey("clusters.id"), nullable=False, index=True)
    similarity_score = Column(Float, nullable=True, doc="Distance/similarity to cluster centroid")
    is_representative = Column(Integer, nullable=False, default=0, doc="1 if this doc is a cluster representative")

    # ── Relationships ─────────────────────────────────────────────────────
    cluster = relationship("Cluster", back_populates="document_clusters")

    __table_args__ = (
        Index("ix_doc_clusters_doc_cluster", "document_id", "cluster_id", unique=True),
    )
