"""
Document service — CRUD operations, search, and pagination for documents.
"""

import math
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc
from typing import Optional

from backend.app.models.document import Document
from backend.app.schemas.common import DocumentFilter


class DocumentService:
    def __init__(self, db: Session):
        self.db = db

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
        if filters.processing_status:
            query = query.filter(Document.processing_status == filters.processing_status)
        if filters.split:
            query = query.filter(Document.split == filters.split)
        if filters.is_synthetic is not None:
            query = query.filter(Document.is_synthetic == filters.is_synthetic)
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.filter(Document.original_text.ilike(search_term))
        if filters.date_from:
            query = query.filter(Document.collected_at >= filters.date_from)
        if filters.date_to:
            query = query.filter(Document.collected_at <= filters.date_to)

        return query

    def get_documents(
        self,
        page: int = 1,
        page_size: int = 50,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        filters: Optional[DocumentFilter] = None,
    ) -> dict:
        """Paginated document list with filters."""
        query = self.db.query(Document)
        query = self._apply_filters(query, filters)

        total = query.count()

        # Sorting
        sort_column = getattr(Document, sort_by, Document.created_at)
        if sort_order == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        # Pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": math.ceil(total / page_size) if page_size > 0 else 0,
        }

    def get_document(self, document_id: int) -> Optional[Document]:
        """Get a single document by ID."""
        return self.db.query(Document).filter(Document.id == document_id).first()

    def search_documents(self, query_text: str, limit: int = 20) -> list[Document]:
        """Full-text search across document texts."""
        search_term = f"%{query_text}%"
        return (
            self.db.query(Document)
            .filter(Document.original_text.ilike(search_term))
            .limit(limit)
            .all()
        )
