"""
Models API — model registry and evaluation results.
Only displays actual metrics from real evaluations.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.model_version import ModelVersion
from backend.app.schemas.analytics import ModelVersionResponse
from backend.app.services.nlp import get_nlp_service

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("", response_model=list[ModelVersionResponse])
def list_models(db: Session = Depends(get_db)):
    """List all registered model versions with their metrics."""
    models = (
        db.query(ModelVersion)
        .order_by(ModelVersion.model_name, ModelVersion.created_at.desc())
        .all()
    )
    return [ModelVersionResponse.model_validate(m) for m in models]


@router.get("/status")
def get_nlp_status():
    """Get current NLP pipeline status."""
    nlp = get_nlp_service()
    return nlp.get_status()
