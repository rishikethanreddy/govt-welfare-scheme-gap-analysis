"""
Geography API — state and district level metrics for awareness gap heatmap.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case, distinct, desc

from backend.app.database import get_db
from backend.app.models.document import Document
from backend.app.services.analytics import AnalyticsService
from backend.app.schemas.common import DocumentFilter

router = APIRouter(prefix="/api/geography", tags=["Geography"])


@router.get("/states")
def get_states(
    scheme: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    awareness_gap: Optional[str] = Query(None),
    gap_type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """State-level geographic aggregation."""
    filters = DocumentFilter(
        scheme=scheme, intent=intent,
        awareness_gap=awareness_gap, gap_type=gap_type,
    )
    svc = AnalyticsService(db)
    states = svc.get_geographic_metrics(filters)
    return {
        "states": states,
        "total_states": len(states),
    }


@router.get("/districts")
def get_districts(
    state: Optional[str] = Query(None),
    scheme: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """District-level geographic aggregation, optionally filtered by state."""
    filters = DocumentFilter(scheme=scheme)
    svc = AnalyticsService(db)
    districts = svc.get_district_metrics(state=state, filters=filters)
    return {
        "districts": districts,
        "total_districts": len(districts),
    }


@router.get("/heatmap")
def get_heatmap(
    level: str = Query("state", regex="^(state|district)$"),
    metric: str = Query("gap_signals", regex="^(gap_signals|gap_rate|records)$"),
    scheme: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Enriched geographic heatmap data with dominant gap type and scheme breakdown.
    """
    filters = DocumentFilter(scheme=scheme)
    svc = AnalyticsService(db)

    if level == "district":
        base_data = svc.get_district_metrics(filters=filters)
    else:
        base_data = svc.get_geographic_metrics(filters=filters)

    # For each region, get dominant gap type and top schemes
    enriched = []
    for region in base_data:
        region_key = region.get("district") or region.get("state")
        state_name = region.get("state")
        
        # Dominant gap type for this region
        q_gap = db.query(
            Document.gap_type,
            func.count(Document.id).label("cnt")
        ).filter(
            func.lower(Document.awareness_gap) == "yes",
            Document.gap_type != None,
            Document.gap_type != "none",
        )

        if level == "district":
            q_gap = q_gap.filter(Document.district == region_key)
        else:
            q_gap = q_gap.filter(Document.state == state_name)

        if scheme:
            q_gap = q_gap.filter(Document.scheme_name == scheme)

        dominant_gap = q_gap.group_by(Document.gap_type).order_by(desc("cnt")).first()

        # Top schemes for this region
        q_schemes = db.query(
            Document.scheme_name,
            func.count(Document.id).label("cnt")
        ).filter(
            Document.scheme_name != None,
        )

        if level == "district":
            q_schemes = q_schemes.filter(Document.district == region_key)
        else:
            q_schemes = q_schemes.filter(Document.state == state_name)

        if scheme:
            q_schemes = q_schemes.filter(Document.scheme_name == scheme)

        top_schemes = q_schemes.group_by(Document.scheme_name).order_by(desc("cnt")).limit(3).all()

        enriched.append({
            **region,
            "dominant_gap_type": dominant_gap[0] if dominant_gap else None,
            "top_schemes": [{"scheme": s[0], "count": s[1]} for s in top_schemes],
        })

    return {
        "level": level,
        "metric": metric,
        "regions": enriched,
        "total_regions": len(enriched),
    }
