"""
Datasets API — upload, import, versioning, and listing.
"""

import os
import shutil
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.config import get_settings
from backend.app.services.dataset import DatasetService
from backend.app.schemas.document import DatasetVersionResponse

router = APIRouter(prefix="/api/datasets", tags=["Datasets"])
settings = get_settings()


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    version: str = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Upload a CSV/JSON dataset file.
    Auto-detects column mapping and imports records.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.allowed_extension_list:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {settings.ALLOWED_EXTENSIONS}",
        )

    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_UPLOAD_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {size_mb:.1f}MB. Max: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Save to uploads directory
    upload_dir = os.path.join(settings.DATA_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Ingest
    svc = DatasetService(db)

    if ext == ".csv":
        result = svc.ingest_csv(file_path, version=version, name=name or file.filename)
    else:
        raise HTTPException(status_code=400, detail=f"Import not yet supported for {ext}")

    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])

    return result


@router.get("", response_model=list[DatasetVersionResponse])
def list_datasets(db: Session = Depends(get_db)):
    """List all dataset versions."""
    svc = DatasetService(db)
    versions = svc.get_versions()
    return [DatasetVersionResponse.model_validate(v) for v in versions]


@router.post("/import-existing")
def import_existing_csv(
    file_path: str = Query(..., description="Path to existing CSV file relative to project root"),
    version: str = Query(None),
    name: str = Query(None),
    db: Session = Depends(get_db),
):
    """
    Import a CSV file that already exists on disk (e.g., the initial dataset).
    Used for development and initial setup.
    """
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")

    svc = DatasetService(db)
    result = svc.ingest_csv(file_path, version=version, name=name)

    if "error" in result:
        raise HTTPException(status_code=409, detail=result["error"])

    return result
