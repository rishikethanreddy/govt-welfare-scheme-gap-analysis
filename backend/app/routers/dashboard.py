"""
Dashboard API — overview metrics, distributions, trends, and recurring issues.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.analytics import AnalyticsService
from backend.app.schemas.common import DocumentFilter

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def _parse_filters(
    scheme: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    awareness_gap: Optional[str] = Query(None),
    gap_type: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
) -> DocumentFilter:
    return DocumentFilter(
        scheme=scheme, state=state, district=district,
        intent=intent, awareness_gap=awareness_gap, gap_type=gap_type,
        language=language, source=source, search=search,
    )


@router.get("/overview")
def get_overview(
    db: Session = Depends(get_db),
    filters: DocumentFilter = Depends(_parse_filters),
):
    """Dashboard overview metrics with optional filters."""
    svc = AnalyticsService(db)
    return svc.get_overview_metrics(filters)


@router.get("/schemes")
def get_scheme_distribution(
    db: Session = Depends(get_db),
    filters: DocumentFilter = Depends(_parse_filters),
):
    """Scheme distribution for dashboard chart."""
    svc = AnalyticsService(db)
    return svc.get_scheme_distribution(filters)


@router.get("/intents")
def get_intent_distribution(
    db: Session = Depends(get_db),
    filters: DocumentFilter = Depends(_parse_filters),
):
    """Intent distribution for dashboard chart."""
    svc = AnalyticsService(db)
    return svc.get_intent_distribution(filters)


@router.get("/gap-types")
def get_gap_type_distribution(
    db: Session = Depends(get_db),
    filters: DocumentFilter = Depends(_parse_filters),
):
    """Gap type distribution for dashboard chart."""
    svc = AnalyticsService(db)
    return svc.get_gap_type_distribution(filters)


@router.get("/recurring-issues")
def get_recurring_issues(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    filters: DocumentFilter = Depends(_parse_filters),
):
    """Top recurring awareness gap issues from actual data."""
    svc = AnalyticsService(db)
    return svc.get_recurring_issues(limit=limit, filters=filters)


@router.get("/filters")
def get_filter_options(db: Session = Depends(get_db)):
    """Available filter values for frontend dropdowns."""
    svc = AnalyticsService(db)
    return svc.get_filter_options()
