"""
Schemes API — scheme registry and intelligence.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case, desc, distinct

from backend.app.database import get_db
from backend.app.models.scheme import Scheme
from backend.app.models.document import Document
from backend.app.schemas.scheme import SchemeResponse, SchemeIntelligenceResponse

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])


@router.get("", response_model=list[SchemeResponse])
def list_schemes(db: Session = Depends(get_db)):
    """List all registered welfare schemes."""
    schemes = db.query(Scheme).filter(Scheme.active == True).order_by(Scheme.display_order, Scheme.name).all()

    if not schemes:
        # Fallback: get distinct scheme names from documents
        scheme_names = (
            db.query(distinct(Document.scheme_name))
            .filter(Document.scheme_name != None)
            .order_by(Document.scheme_name)
            .all()
        )
        return [
            {"id": i, "name": name, "short_name": name, "active": True}
            for i, (name,) in enumerate(scheme_names, 1)
        ]

    return [SchemeResponse.model_validate(s) for s in schemes]


@router.get("/{scheme_id}")
def get_scheme_intelligence(
    scheme_id: str,
    db: Session = Depends(get_db),
):
    """
    Scheme intelligence page — detailed analysis for a single scheme.
    Accepts either numeric ID or scheme name.
    """
    # Try to find by ID first, then by name
    scheme_name = scheme_id
    scheme_obj = None

    try:
        sid = int(scheme_id)
        scheme_obj = db.query(Scheme).filter(Scheme.id == sid).first()
        if scheme_obj:
            scheme_name = scheme_obj.short_name or scheme_obj.name
    except ValueError:
        scheme_obj = db.query(Scheme).filter(
            (Scheme.short_name == scheme_id) | (Scheme.name == scheme_id)
        ).first()
        if scheme_obj:
            scheme_name = scheme_obj.short_name or scheme_obj.name

    # Get document metrics for this scheme
    base = db.query(Document).filter(Document.scheme_name == scheme_name)
    total = base.count()

    if total == 0:
        raise HTTPException(status_code=404, detail=f"No data found for scheme: {scheme_name}")

    gap_signals = base.filter(func.lower(Document.awareness_gap) == "yes").count()

    # Top intents
    top_intents = (
        base.with_entities(Document.intent, func.count(Document.id).label("count"))
        .group_by(Document.intent)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    # Top gap types
    top_gaps = (
        base.filter(Document.gap_type != None, Document.gap_type != "none")
        .with_entities(Document.gap_type, func.count(Document.id).label("count"))
        .group_by(Document.gap_type)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    # Top states
    top_states = (
        base.filter(Document.state != None, Document.state != "Unknown")
        .with_entities(Document.state, func.count(Document.id).label("count"))
        .group_by(Document.state)
        .order_by(desc("count"))
        .limit(5)
        .all()
    )

    # Recurring questions (actual data, not fabricated)
    recurring = (
        base.filter(func.lower(Document.awareness_gap) == "yes")
        .with_entities(Document.original_text, Document.gap_type)
        .limit(10)
        .all()
    )

    # Misconceptions
    misconceptions = (
        base.filter(Document.gap_type == "misconception")
        .with_entities(Document.original_text)
        .limit(5)
        .all()
    )

    return {
        "scheme": {
            "id": scheme_obj.id if scheme_obj else 0,
            "name": scheme_name,
            "short_name": scheme_name,
            "active": True,
        },
        "total_records": total,
        "awareness_gap_signals": gap_signals,
        "gap_rate": round(gap_signals / total * 100, 2) if total > 0 else 0.0,
        "top_intents": [{"intent": r[0], "count": r[1]} for r in top_intents],
        "top_gap_types": [{"gap_type": r[0], "count": r[1]} for r in top_gaps],
        "top_states": [{"state": r[0], "count": r[1]} for r in top_states],
        "recurring_questions": [{"text": r[0], "gap_type": r[1]} for r in recurring],
        "misconceptions": [{"text": r[0]} for r in misconceptions],
    }
