"""
Scraping Orchestrator — manages end-to-end scraping runs:
  Source registration → robots.txt check → scrape → ingest → store → audit
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict
from sqlalchemy.orm import Session

from backend.app.models.source import Source, SourceRun
from backend.app.models.document import Document
from backend.app.models.audit import AuditLog
from backend.app.services.scraper import (
    BaseScraper, RSSScraper, HTMLScraper, APIScraper, LocalDatasetScraper,
    ScrapedRecord, PolicyEngine, WELFARE_SOURCES,
)
from backend.app.services.ingestion import IngestionPipeline
from backend.app.services.nlp import get_nlp_service

logger = logging.getLogger(__name__)


SCRAPER_MAP = {
    "rss": RSSScraper,
    "html": HTMLScraper,
    "api": APIScraper,
    "dataset": LocalDatasetScraper,
}


class ScrapingOrchestrator:
    """Manages scraping runs: registration, execution, storage, auditing."""

    def __init__(self, db: Session):
        self.db = db
        self.pipeline = IngestionPipeline()
        self.policy = PolicyEngine()

    # ── Source Registration ────────────────────────────────────────────

    def register_source(
        self,
        name: str,
        url: str,
        source_type: str = "web",
        scraper_type: str = "html",
        collection_method: str = "scraper",
        schedule: str = "manual",
    ) -> Source:
        """Register a new data source."""
        existing = self.db.query(Source).filter(Source.url == url).first()
        if existing:
            return existing

        # Check robots.txt
        policy = self.policy.check_robots(url)

        source = Source(
            name=name,
            url=url,
            source_type=source_type,
            collection_method=collection_method,
            content_type=scraper_type,
            schedule=schedule,
            robots_checked=policy["robots_checked"],
            crawl_delay=policy["crawl_delay"],
            policy_status="allowed" if policy["allowed"] else "blocked",
            active=policy["allowed"],
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        self._audit("source_registered", "source", str(source.id), f"Registered source: {name}")
        return source

    def register_default_sources(self) -> List[Source]:
        """Register all pre-configured welfare scheme sources."""
        sources = []
        for src_def in WELFARE_SOURCES:
            source = self.register_source(
                name=src_def["name"],
                url=src_def["url"],
                source_type=src_def.get("source_type", "web"),
                scraper_type=src_def.get("scraper_type", "html"),
            )
            sources.append(source)
        return sources

    # ── Scrape Execution ──────────────────────────────────────────────

    def run_scrape(
        self,
        source_id: int,
        max_records: int = 100,
    ) -> Dict:
        """Execute a scraping run for a specific source."""
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {"error": f"Source {source_id} not found"}

        if not source.active:
            return {"error": f"Source '{source.name}' is inactive"}

        if source.policy_status == "blocked":
            return {"error": f"Source '{source.name}' is blocked by robots.txt policy"}

        # Create run record
        run = SourceRun(
            source_id=source.id,
            status="running",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)

        try:
            # Get scraper
            scraper_cls = SCRAPER_MAP.get(source.content_type, HTMLScraper)
            scraper = scraper_cls(name=source.name)

            # Scrape
            logger.info(f"Starting scrape run #{run.id} for source: {source.name}")
            raw_records = scraper.scrape(source.url)
            scraper.close()

            run.urls_discovered = 1
            run.records_extracted = len(raw_records)

            if not raw_records:
                run.status = "completed"
                run.finished_at = datetime.now(timezone.utc)
                self.db.commit()
                return {"status": "completed", "records_extracted": 0, "records_stored": 0}

            # Convert to pipeline format
            pipeline_records = []
            for sr in raw_records[:max_records]:
                pipeline_records.append({
                    "text": sr.text,
                    "scheme_name": sr.scheme_name,
                    "state": sr.state,
                    "district": sr.district,
                    "source_name": sr.source_name,
                    "source_type": sr.source_type,
                    "source_url": sr.source_url,
                    "language": sr.language,
                })

            # Run through ingestion pipeline
            result = self.pipeline.process_records(pipeline_records)

            # Store valid records
            stored = 0
            for rec in result["valid_records"]:
                # Global Duplicate Detection
                text = rec.get("normalized_text") or rec["text"]
                if not text:
                    continue
                
                # Check DB for duplicate text
                existing_doc = self.db.query(Document).filter(
                    Document.normalized_text == text
                ).first()

                if existing_doc:
                    run.duplicates_found = (getattr(run, "duplicates_found", 0) or 0) + 1
                    continue

                # Run NLP classification
                nlp = get_nlp_service()
                analysis = nlp.analyze_text(text)

                doc = Document(
                    original_text=rec["text"],
                    normalized_text=rec.get("normalized_text"),
                    scheme_name=analysis.get("scheme") or rec.get("scheme_name"),
                    state=rec.get("state"),
                    district=rec.get("district"),
                    intent=analysis.get("intent"),
                    awareness_gap=analysis.get("awareness_gap"),
                    gap_type=analysis.get("gap_type"),
                    source_name=rec.get("source_name") or source.name,
                    source_type=rec.get("source_type") or source.source_type,
                    source_url=rec.get("source_url") or source.url,
                    source_id=source.id,
                    scrape_run_id=run.id,
                    language=rec.get("language", "English"),
                    processing_status="imported",
                    pii_detected=rec.get("pii_detected", False),
                    pii_redacted=rec.get("pii_redacted", False),
                    is_duplicate=rec.get("is_duplicate", False),
                    duplicate_group_id=rec.get("duplicate_group_id"),
                    is_synthetic=False,
                    is_demo=False,
                    collected_at=datetime.now(timezone.utc),
                )
                self.db.add(doc)
                stored += 1

            # Update run
            run.status = "completed"
            run.finished_at = datetime.now(timezone.utc)
            run.records_accepted = stored
            run.duplicates_found = len(result["duplicate_records"])
            run.records_rejected = len(result["rejected_records"])

            # Update source stats
            source.total_records_collected = (source.total_records_collected or 0) + stored
            source.total_runs = (source.total_runs or 0) + 1
            source.last_success_at = datetime.now(timezone.utc)

            self.db.commit()

            self._audit(
                "scrape_completed", "source_run", str(run.id),
                f"Scraped {source.name}: {stored} stored, "
                f"{run.duplicates_found} dupes, {run.records_rejected} rejected"
            )

            return {
                "status": "completed",
                "run_id": run.id,
                "records_extracted": run.records_extracted,
                "records_stored": stored,
                "records_duplicate": run.duplicates_found,
                "records_rejected": run.records_rejected,
            }

        except Exception as e:
            run.status = "failed"
            run.error_message = str(e)
            run.finished_at = datetime.now(timezone.utc)
            self.db.commit()
            logger.error(f"Scrape run #{run.id} failed: {e}")
            self._audit("scrape_failed", "source_run", str(run.id), f"Failed: {e}", severity="error")
            return {"error": str(e), "run_id": run.id}

    def run_all_sources(self, max_records_per_source: int = 50) -> Dict:
        """Run scraping for all active sources."""
        active_sources = self.db.query(Source).filter(
            Source.active == True,
            Source.policy_status != "blocked",
        ).all()

        results = {}
        for source in active_sources:
            results[source.name] = self.run_scrape(source.id, max_records=max_records_per_source)

        return results

    # ── Source Management ─────────────────────────────────────────────

    def get_source_runs(self, source_id: int) -> List[SourceRun]:
        return self.db.query(SourceRun).filter(
            SourceRun.source_id == source_id
        ).order_by(SourceRun.started_at.desc()).limit(20).all()

    def recheck_policy(self, source_id: int) -> Dict:
        """Re-check robots.txt policy for a source."""
        source = self.db.query(Source).filter(Source.id == source_id).first()
        if not source:
            return {"error": "Source not found"}

        policy = self.policy.check_robots(source.url)
        source.robots_checked = policy["robots_checked"]
        source.robots_allowed = policy["allowed"]
        source.crawl_delay = policy["crawl_delay"]
        source.policy_status = "allowed" if policy["allowed"] else "blocked"
        self.db.commit()

        return policy

    # ── Audit ─────────────────────────────────────────────────────────

    def _audit(self, action: str, entity_type: str, entity_id: str, description: str, severity: str = "info"):
        log = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            user="scraper",
            severity=severity,
        )
        self.db.add(log)
        try:
            self.db.commit()
        except Exception:
            self.db.rollback()
