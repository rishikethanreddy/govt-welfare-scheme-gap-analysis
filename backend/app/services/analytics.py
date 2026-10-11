"""
Analytics service — dashboard metrics, distributions, and geographic aggregation.

Reuses the query patterns from the original analytics_service.py, expanded
for the full dashboard, scheme intelligence, and geographic intelligence features.
"""

import math
from sqlalchemy.orm import Session
from sqlalchemy import func, case, distinct, desc
from typing import Optional

from backend.app.models.document import Document
from backend.app.models.scheme import Scheme
from backend.app.models.source import Source
from backend.app.schemas.common import DocumentFilter


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    # ── Filter Builder ────────────────────────────────────────────────────

    def _apply_filters(self, query, filters: Optional[DocumentFilter] = None):
        """Apply common filters to a document query."""
        if not filters:
            return query

        if filters.scheme:
            query = query.filter(Document.scheme_name == filters.scheme)
        if filters.state:
            query = query.filter(Document.state == filters.state)
        if filters.district:
            query = query.filter(Document.district == filters.district)
        if filters.intent:
            query = query.filter(Document.intent == filters.intent)
        if filters.awareness_gap:
            query = query.filter(func.lower(Document.awareness_gap) == filters.awareness_gap.lower())
        if filters.gap_type:
            query = query.filter(Document.gap_type == filters.gap_type)
        if filters.language:
            query = query.filter(Document.language == filters.language)
        if filters.source:
            query = query.filter(Document.source_name == filters.source)
        if filters.source_type:
            query = query.filter(Document.source_type == filters.source_type)
        if filters.processing_status:
            query = query.filter(Document.processing_status == filters.processing_status)
        if filters.split:
            query = query.filter(Document.split == filters.split)
        if filters.date_from:
            query = query.filter(Document.collected_at >= filters.date_from)
        if filters.date_to:
            query = query.filter(Document.collected_at <= filters.date_to)
        if filters.is_synthetic is not None:
            query = query.filter(Document.is_synthetic == filters.is_synthetic)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(Document.original_text.ilike(search_term))

        return query

    # ── Overview Metrics ──────────────────────────────────────────────────

    def get_overview_metrics(self, filters: Optional[DocumentFilter] = None) -> dict:
        base_query = self.db.query(Document)
        base_query = self._apply_filters(base_query, filters)

        total_records = base_query.count()

        total_schemes = base_query.query(
            func.count(distinct(Document.scheme_name))
        ).scalar() if hasattr(base_query, 'query') else (
            self.db.query(func.count(distinct(Document.scheme_name)))
            .filter(Document.id.in_(base_query.with_entities(Document.id).subquery().select()))
            .scalar()
        ) if total_records > 0 else 0

        # Simpler approach: count distinct values from filtered set
        total_schemes = self._apply_filters(
            self.db.query(func.count(distinct(Document.scheme_name))), filters
        ).scalar() or 0

        total_states = self._apply_filters(
            self.db.query(func.count(distinct(Document.state))).filter(
                Document.state != None, Document.state != "Unknown"
            ), filters
        ).scalar() or 0

        total_districts = self._apply_filters(
            self.db.query(func.count(distinct(Document.district))).filter(
                Document.district != None, Document.district != "Unknown"
            ), filters
        ).scalar() or 0

        gap_signals = self._apply_filters(
            self.db.query(func.count(Document.id)).filter(
                func.lower(Document.awareness_gap) == "yes"
            ), filters
        ).scalar() or 0

        active_sources = self.db.query(func.count(Source.id)).filter(Source.active == True).scalar() or 0
        total_sources = self.db.query(func.count(Source.id)).scalar() or 0

        gap_rate = round(gap_signals / total_records * 100, 2) if total_records > 0 else 0.0

        return {
            "total_records": total_records,
            "schemes_analyzed": total_schemes,
            "states_covered": total_states,
            "districts_covered": total_districts,
            "awareness_gap_signals": gap_signals,
            "gap_rate": gap_rate,
            "active_sources": active_sources,
            "total_sources": total_sources,
        }

    # ── Scheme Distribution ───────────────────────────────────────────────

    def get_scheme_distribution(self, filters: Optional[DocumentFilter] = None) -> list[dict]:
        query = self.db.query(
            Document.scheme_name,
            func.count(Document.id).label("total"),
            func.sum(
                case((func.lower(Document.awareness_gap) == "yes", 1), else_=0)
            ).label("gaps"),
        ).group_by(Document.scheme_name).order_by(desc("total"))

        query = self._apply_filters(query, filters)
        results = query.all()

        return [
            {
                "scheme": r[0] or "Unknown",
                "total_records": r[1],
                "gap_signals": int(r[2] or 0),
                "gap_rate": round((r[2] or 0) / r[1] * 100, 2) if r[1] > 0 else 0.0,
            }
            for r in results
        ]

    # ── Intent Distribution ───────────────────────────────────────────────

    def get_intent_distribution(self, filters: Optional[DocumentFilter] = None) -> list[dict]:
        query = self.db.query(
            Document.intent,
            func.count(Document.id).label("count"),
        ).group_by(Document.intent).order_by(desc("count"))

        query = self._apply_filters(query, filters)
        results = query.all()

        total = sum(r[1] for r in results) or 1

        return [
            {
                "intent": r[0] or "unknown",
                "count": r[1],
                "percentage": round(r[1] / total * 100, 1),
            }
            for r in results
        ]

    # ── Gap Type Distribution ─────────────────────────────────────────────

    def get_gap_type_distribution(self, filters: Optional[DocumentFilter] = None) -> list[dict]:
        query = self.db.query(
            Document.gap_type,
            func.count(Document.id).label("count"),
        ).filter(
            Document.gap_type != None, Document.gap_type != "none"
        ).group_by(Document.gap_type).order_by(desc("count"))

        query = self._apply_filters(query, filters)
        results = query.all()

        total = sum(r[1] for r in results) or 1

        return [
            {
                "gap_type": r[0],
                "count": r[1],
                "percentage": round(r[1] / total * 100, 1),
            }
            for r in results
        ]

    # ── Geographic Metrics ────────────────────────────────────────────────

    def get_geographic_metrics(self, filters: Optional[DocumentFilter] = None) -> list[dict]:
        query = self.db.query(
            Document.state,
            func.count(Document.id).label("total"),
            func.sum(
                case((func.lower(Document.awareness_gap) == "yes", 1), else_=0)
            ).label("gaps"),
        ).filter(
            Document.state != None, Document.state != "Unknown"
        ).group_by(Document.state).order_by(desc("total"))

        query = self._apply_filters(query, filters)
        results = query.all()

        return [
            {
                "state": r[0],
                "total_records": r[1],
                "gap_signals": int(r[2] or 0),
                "gap_rate": round((r[2] or 0) / r[1] * 100, 2) if r[1] > 0 else 0.0,
            }
            for r in results
        ]

    # ── District Metrics ──────────────────────────────────────────────────

    def get_district_metrics(self, state: Optional[str] = None, filters: Optional[DocumentFilter] = None) -> list[dict]:
        query = self.db.query(
            Document.state,
            Document.district,
            func.count(Document.id).label("total"),
            func.sum(
                case((func.lower(Document.awareness_gap) == "yes", 1), else_=0)
            ).label("gaps"),
        ).filter(
            Document.district != None, Document.district != "Unknown"
        ).group_by(Document.state, Document.district).order_by(desc("total"))

        if state:
            query = query.filter(Document.state == state)

        query = self._apply_filters(query, filters)
        results = query.all()

        return [
            {
                "state": r[0],
                "district": r[1],
                "total_records": r[2],
                "gap_signals": int(r[3] or 0),
                "gap_rate": round((r[3] or 0) / r[2] * 100, 2) if r[2] > 0 else 0.0,
            }
            for r in results
        ]

    # ── Filter Options (for frontend dropdowns) ──────────────────────────

    def get_filter_options(self) -> dict:
        """Returns distinct values for each filterable field."""
        def _distinct_values(column):
            results = self.db.query(distinct(column)).filter(column != None).order_by(column).all()
            return [r[0] for r in results if r[0]]

        return {
            "schemes": _distinct_values(Document.scheme_name),
            "states": [s for s in _distinct_values(Document.state) if s != "Unknown"],
            "districts": [d for d in _distinct_values(Document.district) if d != "Unknown"],
            "intents": _distinct_values(Document.intent),
            "gap_types": [g for g in _distinct_values(Document.gap_type) if g != "none"],
            "languages": _distinct_values(Document.language),
            "sources": _distinct_values(Document.source_name),
            "source_types": _distinct_values(Document.source_type),
        }

    # ── Recurring Issues ──────────────────────────────────────────────────

    def get_recurring_issues(self, limit: int = 10, filters: Optional[DocumentFilter] = None) -> list[dict]:
        """
        Returns the most common gap-related texts grouped by scheme and gap_type.
        These represent recurring awareness issues from actual data.
        """
        query = self.db.query(
            Document.original_text,
            Document.scheme_name,
            Document.intent,
            Document.gap_type,
            Document.state,
        ).filter(
            func.lower(Document.awareness_gap) == "yes"
        ).order_by(Document.id)

        query = self._apply_filters(query, filters)
        results = query.limit(limit * 3).all()  # Fetch extra to deduplicate

        seen = set()
        issues = []
        for r in results:
            text_key = (r[0] or "")[:100].lower().strip()
            if text_key not in seen and text_key:
                seen.add(text_key)
                issues.append({
                    "text": r[0],
                    "scheme": r[1],
                    "intent": r[2],
                    "gap_type": r[3],
                    "states": [r[4]] if r[4] and r[4] != "Unknown" else [],
                })
            if len(issues) >= limit:
                break

        return issues
