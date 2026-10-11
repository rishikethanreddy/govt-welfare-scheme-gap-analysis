"""
Collection API — campaign management, source registration, collection execution, diagnostics.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.database import get_db
from backend.app.models.crawl import CrawlUrl, CrawlPage, CollectionCampaign
from backend.app.models.source import Source, SourceRun
from backend.app.models.document import Document
from backend.app.services.crawl_engine import CollectionOrchestrator, SOURCE_REGISTRY, SCHEME_TOPICS

router = APIRouter(prefix="/api/collection", tags=["collection"])


# ── Campaign Management ────────────────────────────────────────────────

@router.post("/campaigns")
def create_campaign(
    name: str = Query(...),
    schemes: Optional[str] = Query(None, description="Comma-separated scheme names"),
    max_urls: int = Query(5000),
    max_depth: int = Query(3),
    max_pages_per_source: int = Query(200),
    db: Session = Depends(get_db),
):
    """Create a new collection campaign."""
    scheme_list = [s.strip() for s in schemes.split(",")] if schemes else None
    orch = CollectionOrchestrator(db)
    campaign = orch.create_campaign(
        name=name, schemes=scheme_list,
        max_urls=max_urls, max_depth=max_depth,
        max_pages_per_source=max_pages_per_source,
    )
    return {
        "id": campaign.id,
        "name": campaign.name,
        "status": campaign.status,
        "schemes": campaign.schemes,
        "max_urls": campaign.max_urls,
    }


@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    """List all collection campaigns."""
    campaigns = db.query(CollectionCampaign).order_by(CollectionCampaign.created_at.desc()).all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "status": c.status,
            "urls_discovered": c.urls_discovered,
            "urls_accepted": c.urls_accepted,
            "pages_downloaded": c.pages_downloaded,
            "pages_useful": c.pages_useful,
            "records_extracted": c.records_extracted,
            "records_duplicate": c.records_duplicate,
            "records_rejected": c.records_rejected,
            "records_final": c.records_final,
            "started_at": c.started_at,
            "finished_at": c.finished_at,
            "created_at": c.created_at,
        }
        for c in campaigns
    ]


@router.get("/campaigns/{campaign_id}")
def get_campaign(campaign_id: int, db: Session = Depends(get_db)):
    """Get campaign details with funnel diagnostics."""
    orch = CollectionOrchestrator(db)
    return orch.get_campaign_funnel(campaign_id)


@router.post("/campaigns/{campaign_id}/run")
def run_campaign(campaign_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Execute a collection campaign (runs in background)."""
    campaign = db.query(CollectionCampaign).filter(CollectionCampaign.id == campaign_id).first()
    if not campaign:
        return {"error": "Campaign not found"}
    if campaign.status in ("collecting", "discovering", "processing"):
        return {"error": "Campaign is already running"}

    # Run synchronously for now (can be moved to background worker)
    orch = CollectionOrchestrator(db)
    result = orch.run_campaign(campaign_id)
    return result


@router.post("/campaigns/{campaign_id}/run-async")
def run_campaign_async(campaign_id: int, db: Session = Depends(get_db)):
    """Queue a campaign for background execution by the decoupled worker."""
    campaign = db.query(CollectionCampaign).filter(CollectionCampaign.id == campaign_id).first()
    if not campaign:
        return {"error": "Campaign not found"}

    campaign.status = "pending"
    db.commit()

    return {"status": "queued", "campaign_id": campaign_id}


# ── Source Management ──────────────────────────────────────────────────

@router.post("/register-all-sources")
def register_all_sources(db: Session = Depends(get_db)):
    """Register all 60+ sources from the expanded registry."""
    orch = CollectionOrchestrator(db)
    sources = orch.register_all_sources()
    return {
        "registered": len(sources),
        "sources": [
            {"id": s.id, "name": s.name, "policy_status": s.policy_status, "active": s.active}
            for s in sources
        ]
    }


@router.get("/source-registry")
def get_source_registry():
    """Get the full source registry (before registration)."""
    categories = {}
    for src in SOURCE_REGISTRY:
        cat = src.get("category", "uncategorized")
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "name": src["name"],
            "url": src["url"],
            "source_type": src["source_type"],
            "scraper_type": src["scraper_type"],
            "priority": src.get("priority", 5),
        })
    return {
        "total_sources": len(SOURCE_REGISTRY),
        "categories": categories,
    }


@router.get("/schemes")
def get_available_schemes():
    """Get all schemes with their topic families."""
    return {
        scheme: {
            "topics_en": topics.get("en", []),
            "topics_hi": topics.get("hi", []),
            "total_topics": sum(len(v) for v in topics.values()),
        }
        for scheme, topics in SCHEME_TOPICS.items()
    }


# ── Diagnostics ────────────────────────────────────────────────────────

@router.get("/overview")
def collection_overview(db: Session = Depends(get_db)):
    """Global collection dashboard metrics."""
    total_sources = db.query(func.count(Source.id)).filter(Source.active == True).scalar() or 0
    total_urls = db.query(func.count(CrawlUrl.id)).scalar() or 0
    total_pages = db.query(func.count(CrawlPage.id)).scalar() or 0
    total_documents = db.query(func.count(Document.id)).filter(Document.is_synthetic == False).scalar() or 0
    total_campaigns = db.query(func.count(CollectionCampaign.id)).scalar() or 0

    # URL status breakdown
    url_statuses = dict(
        db.query(CrawlUrl.status, func.count(CrawlUrl.id))
        .group_by(CrawlUrl.status).all()
    )

    # Records by source
    records_by_source = (
        db.query(Source.name, func.count(Document.id))
        .join(Document, Document.source_id == Source.id)
        .group_by(Source.name)
        .order_by(func.count(Document.id).desc())
        .limit(20)
        .all()
    )

    # Records by scheme
    records_by_scheme = (
        db.query(Document.scheme_name, func.count(Document.id))
        .filter(Document.scheme_name != None)
        .group_by(Document.scheme_name)
        .order_by(func.count(Document.id).desc())
        .all()
    )

    return {
        "active_sources": total_sources,
        "total_urls_discovered": total_urls,
        "total_pages_collected": total_pages,
        "total_documents": total_documents,
        "total_campaigns": total_campaigns,
        "url_status_breakdown": url_statuses,
        "records_by_source": [{"source": s, "count": c} for s, c in records_by_source],
        "records_by_scheme": [{"scheme": s or "Unknown", "count": c} for s, c in records_by_scheme],
    }


@router.get("/funnel")
def pipeline_funnel(db: Session = Depends(get_db)):
    """Global pipeline diagnostic funnel — shows where records are gained/lost."""
    urls_discovered = db.query(func.count(CrawlUrl.id)).scalar() or 0
    urls_queued = db.query(func.count(CrawlUrl.id)).filter(CrawlUrl.status == "queued").scalar() or 0
    urls_success = db.query(func.count(CrawlUrl.id)).filter(CrawlUrl.status == "success").scalar() or 0
    urls_failed = db.query(func.count(CrawlUrl.id)).filter(CrawlUrl.status == "failed").scalar() or 0
    urls_blocked = db.query(func.count(CrawlUrl.id)).filter(CrawlUrl.status == "blocked").scalar() or 0

    pages_total = db.query(func.count(CrawlPage.id)).scalar() or 0
    pages_useful = db.query(func.count(CrawlPage.id)).filter(CrawlPage.has_useful_content == True).scalar() or 0

    total_records = db.query(func.count(Document.id)).filter(Document.is_synthetic == False).scalar() or 0
    duplicate_records = db.query(func.count(Document.id)).filter(Document.is_duplicate == True).scalar() or 0

    return {
        "funnel": [
            {"stage": "URLs Discovered", "count": urls_discovered},
            {"stage": "URLs Queued", "count": urls_queued},
            {"stage": "URLs Successfully Fetched", "count": urls_success},
            {"stage": "URLs Failed", "count": urls_failed, "delta": True},
            {"stage": "URLs Blocked", "count": urls_blocked, "delta": True},
            {"stage": "Pages Downloaded", "count": pages_total},
            {"stage": "Pages With Useful Content", "count": pages_useful},
            {"stage": "Total Records (incl. dupes)", "count": total_records + duplicate_records},
            {"stage": "Duplicates", "count": duplicate_records, "delta": True},
            {"stage": "Final Unique Records", "count": total_records, "highlight": True},
        ],
    }


@router.get("/live-feed")
def live_feed(db: Session = Depends(get_db)):
    """Real-time feed of the scraping process."""
    # Recent URLs
    recent_urls = (
        db.query(CrawlUrl)
        .order_by(CrawlUrl.created_at.desc())
        .limit(10)
        .all()
    )
    
    # Recent Documents
    recent_documents = (
        db.query(Document)
        .order_by(Document.collected_at.desc())
        .limit(10)
        .all()
    )
    
    # Active Campaigns
    active_campaigns = (
        db.query(CollectionCampaign)
        .filter(CollectionCampaign.status.in_(["pending", "discovering", "collecting"]))
        .all()
    )
    
    # Global Stats
    total_docs = db.query(func.count(Document.id)).scalar() or 0
    total_gaps = db.query(func.count(Document.id)).filter(func.lower(Document.awareness_gap) == "yes").scalar() or 0
    
    return {
        "stats": {
            "total_documents": total_docs,
            "total_gaps": total_gaps
        },
        "recent_urls": [
            {
                "url": u.url,
                "status": u.status,
                "time": u.created_at,
            }
            for u in recent_urls
        ],
        "recent_documents": [
            {
                "text": d.original_text,
                "scheme": d.scheme_name,
                "state": d.state,
                "district": d.district,
                "intent": d.intent,
                "gap": d.awareness_gap,
                "gap_type": d.gap_type,
                "source": d.source_name,
                "time": d.collected_at,
            }
            for d in recent_documents
        ],
        "active_campaigns": [
            {
                "id": c.id,
                "name": c.name,
                "status": c.status,
                "urls_discovered": c.urls_discovered,
                "urls_accepted": c.urls_accepted,
                "records_final": c.records_final,
            }
            for c in active_campaigns
        ]
    }


@router.get("/worker-status")
def worker_status(db: Session = Depends(get_db)):
    """Returns the status of the background worker / auto-pilot."""
    import os
    
    is_auto_pilot = os.path.exists(".autopilot")
    
    active_campaigns = db.query(func.count(CollectionCampaign.id)).filter(
        CollectionCampaign.status.in_(["pending", "discovering", "collecting"])
    ).scalar() or 0
    
    return {
        "auto_pilot_enabled": is_auto_pilot,
        "active_campaigns": active_campaigns,
        "status": "idle" if active_campaigns == 0 and not is_auto_pilot else "running",
    }

@router.post("/toggle-autopilot")
def toggle_autopilot(enable: bool = Query(...)):
    import os
    if enable:
        open(".autopilot", "w").close()
    else:
        if os.path.exists(".autopilot"):
            os.remove(".autopilot")
    return {"auto_pilot_enabled": enable}
