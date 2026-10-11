"""
System API — system health, audit logs, and administration.
"""

from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from backend.app.database import get_db
from backend.app.config import get_settings
from backend.app.models.document import Document
from backend.app.models.source import Source
from backend.app.models.processing import ProcessingJob
from backend.app.models.audit import AuditLog
from backend.app.schemas.common import SystemHealthResponse

router = APIRouter(prefix="/api/system", tags=["System"])
settings = get_settings()


@router.get("/health", response_model=SystemHealthResponse)
def system_health(db: Session = Depends(get_db)):
    """Comprehensive system health check with actual service status."""
    # Database check
    db_status = "unknown"
    db_type = "sqlite" if settings.is_sqlite else "postgresql"
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Document count
    total_docs = 0
    try:
        total_docs = db.query(func.count(Document.id)).scalar() or 0
    except Exception:
        pass

    # Source count
    total_sources = 0
    try:
        total_sources = db.query(func.count(Source.id)).scalar() or 0
    except Exception:
        pass

    # Active jobs
    active_jobs = 0
    try:
        active_jobs = (
            db.query(func.count(ProcessingJob.id))
            .filter(ProcessingJob.status.in_(["pending", "running"]))
            .scalar() or 0
        )
    except Exception:
        pass

    # Failed jobs in last 24h
    failed_24h = 0
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        failed_24h = (
            db.query(func.count(ProcessingJob.id))
            .filter(ProcessingJob.status == "failed", ProcessingJob.created_at >= cutoff)
            .scalar() or 0
        )
    except Exception:
        pass

    return SystemHealthResponse(
        api_status="healthy",
        database_status=db_status,
        database_type=db_type,
        total_documents=total_docs,
        total_sources=total_sources,
        active_jobs=active_jobs,
        failed_jobs_24h=failed_24h,
        timestamp=datetime.now(timezone.utc),
    )


@router.get("/audit-logs")
def get_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    action: str = Query(None),
    db: Session = Depends(get_db),
):
    """Get recent audit log entries."""
    query = db.query(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        query = query.filter(AuditLog.action == action)
    logs = query.limit(limit).all()
    return [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "severity": log.severity,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
