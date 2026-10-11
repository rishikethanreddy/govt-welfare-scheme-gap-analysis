"""
Crawl models — URL frontier, crawl pages, raw documents, collection campaigns.
"""

from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, DateTime,
    ForeignKey, Index, JSON
)
from sqlalchemy.orm import relationship
from backend.app.database import Base


class CrawlUrl(Base):
    """URL frontier — every URL discovered for potential crawling."""
    __tablename__ = "crawl_urls"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True, index=True)
    campaign_id = Column(Integer, ForeignKey("collection_campaigns.id"), nullable=True, index=True)

    url = Column(String(2048), nullable=False, index=True)
    canonical_url = Column(String(2048), nullable=True)
    domain = Column(String(255), nullable=True, index=True)

    # Discovery
    discovered_from = Column(String(2048), nullable=True, doc="Parent URL that led to this")
    discovery_method = Column(
        String(30), nullable=False, default="manual",
        doc="manual / sitemap / rss / pagination / internal_link / search / topic_query"
    )
    discovery_query = Column(String(500), nullable=True, doc="Search query that found this URL")
    depth = Column(Integer, nullable=False, default=0)

    # Priority & Status
    priority = Column(Integer, nullable=False, default=5, doc="1=highest, 10=lowest")
    status = Column(
        String(20), nullable=False, default="discovered", index=True,
        doc="discovered / queued / processing / success / failed / blocked / irrelevant / duplicate"
    )

    # Attempt tracking
    attempt_count = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime, nullable=True)
    next_attempt_at = Column(DateTime, nullable=True)

    # Response
    http_status = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    content_hash = Column(String(64), nullable=True, doc="SHA256 of response body for change detection")
    content_length = Column(Integer, nullable=True)

    # Results
    records_extracted = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, nullable=False,
                        default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_crawl_urls_status_priority", "status", "priority"),
        Index("ix_crawl_urls_domain_status", "domain", "status"),
        Index("ix_crawl_urls_campaign", "campaign_id", "status"),
    )


class CrawlPage(Base):
    """Downloaded page content and metadata."""
    __tablename__ = "crawl_pages"

    id = Column(Integer, primary_key=True, index=True)
    crawl_url_id = Column(Integer, ForeignKey("crawl_urls.id"), nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=True)
    campaign_id = Column(Integer, ForeignKey("collection_campaigns.id"), nullable=True)
    run_id = Column(Integer, ForeignKey("source_runs.id"), nullable=True)

    url = Column(String(2048), nullable=False)
    http_status = Column(Integer, nullable=True)
    content_type = Column(String(100), nullable=True)
    content_hash = Column(String(64), nullable=True)
    content_length = Column(Integer, nullable=True)

    # Classification
    page_type = Column(
        String(30), nullable=True,
        doc="article / faq / discussion / listing / category / pdf / dataset / unknown"
    )
    has_useful_content = Column(Boolean, nullable=False, default=False)
    relevance_score = Column(Float, nullable=True)

    # Extraction results
    records_extracted = Column(Integer, nullable=False, default=0)
    extraction_method = Column(String(30), nullable=True, doc="html_faq / html_article / rss / pdf_text / api / question_split")

    # Metadata
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    language = Column(String(20), nullable=True)

    fetched_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    processed_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_crawl_pages_source_type", "source_id", "page_type"),
    )


class CollectionCampaign(Base):
    """A collection campaign — a named, configured batch collection effort."""
    __tablename__ = "collection_campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Config
    schemes = Column(JSON, nullable=True, doc="List of scheme names to target")
    topics = Column(JSON, nullable=True, doc="List of topic strings")
    languages = Column(JSON, nullable=True, doc="List of language codes")
    source_ids = Column(JSON, nullable=True, doc="List of source IDs to include")
    max_urls = Column(Integer, nullable=True, default=5000)
    max_depth = Column(Integer, nullable=True, default=3)
    max_pages_per_source = Column(Integer, nullable=True, default=200)

    # Status
    status = Column(
        String(20), nullable=False, default="created",
        doc="created / discovering / collecting / processing / completed / paused / failed"
    )

    # Metrics
    urls_discovered = Column(Integer, nullable=False, default=0)
    urls_accepted = Column(Integer, nullable=False, default=0)
    pages_downloaded = Column(Integer, nullable=False, default=0)
    pages_useful = Column(Integer, nullable=False, default=0)
    records_extracted = Column(Integer, nullable=False, default=0)
    records_duplicate = Column(Integer, nullable=False, default=0)
    records_rejected = Column(Integer, nullable=False, default=0)
    records_final = Column(Integer, nullable=False, default=0)

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
