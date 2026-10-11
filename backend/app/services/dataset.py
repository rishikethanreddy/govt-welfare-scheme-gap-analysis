"""
Dataset service — CSV/JSON ingestion, validation, and versioning.

Handles the full pipeline: upload → column mapping → validation → dedup → DB.
"""

import os
import hashlib
import math
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from backend.app.models.document import Document
from backend.app.models.processing import DatasetVersion
from backend.app.models.audit import AuditLog


class DatasetService:
    def __init__(self, db: Session):
        self.db = db

    # ── Known column aliases ──────────────────────────────────────────────
    COLUMN_MAP = {
        # Canonical name → list of possible aliases
        "text": ["text", "query", "question", "content", "description", "message", "body"],
        "scheme": ["scheme", "scheme_name", "welfare_scheme", "program"],
        "intent": ["intent", "intent_label", "category"],
        "awareness_gap": ["awareness_gap", "gap", "has_gap"],
        "gap_type": ["gap_type", "gap_category", "awareness_gap_type"],
        "state": ["state", "state_name", "region"],
        "district": ["district", "district_name"],
        "source": ["source", "data_source", "origin"],
        "source_type": ["source_type", "type"],
        "language": ["language", "lang"],
        "source_url": ["source_url", "url", "link"],
        "is_synthetic": ["is_synthetic", "synthetic"],
        "confidence": ["confidence", "confidence_level"],
        "notes": ["notes", "remarks", "comment"],
        "split": ["split", "data_split"],
    }

    def auto_map_columns(self, csv_columns: list[str]) -> dict[str, Optional[str]]:
        """Auto-detect column mapping from CSV headers to canonical fields."""
        mapping = {}
        csv_lower = {c.lower().strip(): c for c in csv_columns}

        for canonical, aliases in self.COLUMN_MAP.items():
            matched = None
            for alias in aliases:
                if alias in csv_lower:
                    matched = csv_lower[alias]
                    break
            mapping[canonical] = matched

        return mapping

    def _next_version(self) -> str:
        """Generate the next dataset version string."""
        latest = (
            self.db.query(DatasetVersion)
            .order_by(DatasetVersion.id.desc())
            .first()
        )
        if not latest:
            return "v1.0"

        # Parse version number
        try:
            version_num = float(latest.version.replace("v", ""))
            return f"v{version_num + 1.0:.1f}"
        except (ValueError, AttributeError):
            return f"v{(latest.id or 0) + 1}.0"

    def _content_hash(self, text: str) -> str:
        """Generate content hash for deduplication."""
        normalized = text.lower().strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]

    def ingest_csv(
        self,
        file_path: str,
        column_mapping: Optional[dict] = None,
        version: Optional[str] = None,
        name: Optional[str] = None,
    ) -> dict:
        """
        Ingest a CSV file into the database.

        Returns a summary of the import operation.
        """
        df = pd.read_csv(file_path)

        # Auto-detect mapping if not provided
        if not column_mapping:
            column_mapping = self.auto_map_columns(list(df.columns))

        # Create dataset version
        version = version or self._next_version()

        # Check if version already exists
        existing = self.db.query(DatasetVersion).filter(DatasetVersion.version == version).first()
        if existing:
            return {
                "error": f"Dataset version {version} already exists.",
                "dataset_version_id": existing.id,
            }

        dataset_version = DatasetVersion(
            version=version,
            name=name or os.path.basename(file_path),
            source_file=os.path.basename(file_path),
            source_type="csv_upload",
            record_count=len(df),
            processing_status="importing",
        )
        self.db.add(dataset_version)
        self.db.commit()
        self.db.refresh(dataset_version)

        # Process records
        valid_count = 0
        duplicate_count = 0
        rejected_count = 0
        seen_hashes = set()

        # Get existing content hashes for deduplication
        existing_hashes = set(
            r[0] for r in
            self.db.query(Document.duplicate_group_id)
            .filter(Document.duplicate_group_id != None)
            .all()
        )

        documents = []
        for _, row in df.iterrows():
            row_dict = {k: (v if pd.notna(v) else None) for k, v in row.to_dict().items()}

            # Get text through column mapping
            text_col = column_mapping.get("text")
            text = row_dict.get(text_col, "") if text_col else ""

            if not text or not str(text).strip():
                rejected_count += 1
                continue

            text = str(text).strip()

            # Deduplication
            content_hash = self._content_hash(text)
            is_dup = content_hash in seen_hashes or content_hash in existing_hashes
            if is_dup:
                duplicate_count += 1

            seen_hashes.add(content_hash)

            # Build document
            def _get(canonical_name):
                col = column_mapping.get(canonical_name)
                return str(row_dict.get(col, "")).strip() if col and row_dict.get(col) is not None else None

            is_synth_val = _get("is_synthetic")
            is_synthetic = is_synth_val.lower() in ("yes", "true", "1") if is_synth_val else False

            doc = Document(
                original_text=text,
                normalized_text=None,  # Will be set by NLP pipeline
                scheme_name=_get("scheme"),
                intent=_get("intent"),
                awareness_gap=_get("awareness_gap"),
                gap_type=_get("gap_type"),
                state=_get("state"),
                district=_get("district"),
                source_name=_get("source"),
                source_type=_get("source_type"),
                language=_get("language") or "en",
                source_url=_get("source_url"),
                confidence=_get("confidence"),
                notes=_get("notes"),
                split=_get("split"),
                is_synthetic=is_synthetic,
                is_duplicate=is_dup,
                duplicate_group_id=content_hash,
                original_csv_id=str(row_dict.get("id", "")),
                dataset_version_id=dataset_version.id,
                processing_status="imported",
                collected_at=datetime.now(timezone.utc),
            )
            documents.append(doc)
            valid_count += 1

        # Bulk insert
        if documents:
            self.db.bulk_save_objects(documents)

        # Update dataset version
        dataset_version.valid_records = valid_count
        dataset_version.duplicate_records = duplicate_count
        dataset_version.rejected_records = rejected_count
        dataset_version.processing_status = "imported"
        self.db.commit()

        # Audit log
        audit = AuditLog(
            action="dataset_import",
            entity_type="dataset",
            entity_id=str(dataset_version.id),
            description=f"Imported {valid_count} records from {os.path.basename(file_path)}",
            details=f'{{"version": "{version}", "total": {len(df)}, "valid": {valid_count}, "duplicates": {duplicate_count}, "rejected": {rejected_count}}}',
        )
        self.db.add(audit)
        self.db.commit()

        return {
            "dataset_version_id": dataset_version.id,
            "version": version,
            "total_records": len(df),
            "valid_records": valid_count,
            "duplicate_records": duplicate_count,
            "rejected_records": rejected_count,
            "processing_status": "imported",
        }

    def get_versions(self) -> list[DatasetVersion]:
        """List all dataset versions."""
        return (
            self.db.query(DatasetVersion)
            .order_by(DatasetVersion.id.desc())
            .all()
        )
