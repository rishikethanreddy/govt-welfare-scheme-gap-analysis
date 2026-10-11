"""
Documents API — paginated listing, detail, and search.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.services.document import DocumentService
from backend.app.schemas.document import DocumentResponse, DocumentListResponse
from backend.app.schemas.common import DocumentFilter

router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.get("", response_model=DocumentListResponse)
def list_documents(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    scheme: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    district: Optional[str] = Query(None),
    intent: Optional[str] = Query(None),
    awareness_gap: Optional[str] = Query(None),
    gap_type: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    processing_status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    split: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """Paginated document listing with filters and sorting."""
    filters = DocumentFilter(
        scheme=scheme, state=state, district=district,
        intent=intent, awareness_gap=awareness_gap, gap_type=gap_type,
        language=language, source=source, processing_status=processing_status,
        search=search, split=split,
    )
    svc = DocumentService(db)
    result = svc.get_documents(
        page=page, page_size=page_size,
        sort_by=sort_by, sort_order=sort_order,
        filters=filters,
    )

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in result["items"]],
        total=result["total"],
        page=result["page"],
        page_size=result["page_size"],
        total_pages=result["total_pages"],
    )


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a single document by ID with full details."""
    svc = DocumentService(db)
    doc = svc.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)
