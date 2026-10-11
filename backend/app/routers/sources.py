"""
Sources API — source management, scraping execution, run history.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.source import Source, SourceRun
from backend.app.services.orchestrator import ScrapingOrchestrator

router = APIRouter(prefix="/api/sources", tags=["Sources"])


@router.get("")
def list_sources(db: Session = Depends(get_db)):
    """List all registered data sources."""
    sources = db.query(Source).order_by(Source.name).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "source_type": s.source_type,
            "collection_method": s.collection_method,
            "scraper_type": s.content_type,
            "schedule": s.schedule,
            "robots_checked": s.robots_checked,
            "policy_status": s.policy_status,
            "crawl_delay": s.crawl_delay,
            "active": s.active,
            "total_records_collected": s.total_records_collected or 0,
            "total_runs": s.total_runs or 0,
            "last_collected_at": s.last_success_at,
        }
        for s in sources
    ]


@router.post("/register")
def register_source(
    name: str = Query(...),
    url: str = Query(...),
    source_type: str = Query("web"),
    scraper_type: str = Query("html", alias="scraper_type"),
    db: Session = Depends(get_db),
):
    """Register a new data source with automatic robots.txt check."""
    orch = ScrapingOrchestrator(db)
    source = orch.register_source(name, url, source_type, scraper_type)
    return {
        "id": source.id,
        "name": source.name,
        "policy_status": source.policy_status,
        "active": source.active,
    }


@router.post("/register-defaults")
def register_default_sources(db: Session = Depends(get_db)):
    """Register all pre-configured welfare scheme sources."""
    orch = ScrapingOrchestrator(db)
    sources = orch.register_default_sources()
    return {
        "registered": len(sources),
        "sources": [{"id": s.id, "name": s.name, "policy_status": s.policy_status} for s in sources],
    }


@router.post("/{source_id}/scrape")
def run_scrape(
    source_id: int,
    max_records: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Trigger a scraping run for a specific source."""
    orch = ScrapingOrchestrator(db)
    result = orch.run_scrape(source_id, max_records=max_records)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/scrape-all")
def run_all_sources(
    max_records: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Trigger scraping for all active sources."""
    orch = ScrapingOrchestrator(db)
    results = orch.run_all_sources(max_records_per_source=max_records)
    return {
        "sources_scraped": len(results),
        "results": results,
    }


@router.get("/{source_id}")
def get_source(source_id: int, db: Session = Depends(get_db)):
    """Get source details."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return {
        "id": source.id,
        "name": source.name,
        "url": source.url,
        "source_type": source.source_type,
        "collection_method": source.collection_method,
        "scraper_type": source.content_type,
        "policy_status": source.policy_status,
        "robots_checked": source.robots_checked,
        "crawl_delay": source.crawl_delay,
        "active": source.active,
        "total_records_collected": source.total_records_collected or 0,
        "total_runs": source.total_runs or 0,
        "last_collected_at": source.last_success_at,
    }


@router.get("/{source_id}/runs")
def get_source_runs(source_id: int, db: Session = Depends(get_db)):
    """Get scraping run history for a source."""
    orch = ScrapingOrchestrator(db)
    runs = orch.get_source_runs(source_id)
    return [
        {
            "id": r.id,
            "status": r.status,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "urls_discovered": r.urls_discovered,
            "records_extracted": r.records_extracted,
            "records_stored": r.records_accepted,
            "records_duplicate": r.duplicates_found,
            "records_rejected": r.records_rejected,
            "error": r.error_message,
        }
        for r in runs
    ]


@router.post("/{source_id}/recheck-policy")
def recheck_policy(source_id: int, db: Session = Depends(get_db)):
    """Re-check robots.txt policy for a source."""
    orch = ScrapingOrchestrator(db)
    result = orch.recheck_policy(source_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.patch("/{source_id}/toggle")
def toggle_source(source_id: int, db: Session = Depends(get_db)):
    """Enable/disable a source."""
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.active = not source.active
    db.commit()
    return {"id": source.id, "active": source.active}
