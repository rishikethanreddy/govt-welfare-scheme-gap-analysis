"""Data ingestion pipeline: validation, normalization, deduplication, PII redaction."""
import re
import hashlib
import csv
import io
from typing import List, Dict, Tuple, Optional
from datetime import datetime


class TextValidator:
    """Validates incoming text records."""

    MIN_TEXT_LENGTH = 10
    MAX_TEXT_LENGTH = 10000
    REQUIRED_FIELDS = ["text"]

    @classmethod
    def validate(cls, record: Dict) -> Tuple[bool, Optional[str]]:
        text = record.get("text", "").strip()
        if not text:
            return False, "Empty text field"
        if len(text) < cls.MIN_TEXT_LENGTH:
            return False, f"Text too short ({len(text)} < {cls.MIN_TEXT_LENGTH})"
        if len(text) > cls.MAX_TEXT_LENGTH:
            return False, f"Text too long ({len(text)} > {cls.MAX_TEXT_LENGTH})"
        # Check for binary/garbled content
        non_printable = sum(1 for c in text if not c.isprintable() and c not in '\n\r\t')
        if non_printable / max(len(text), 1) > 0.1:
            return False, "Too many non-printable characters"
        return True, None


class TextNormalizer:
    """Normalizes text for consistent processing."""

    @staticmethod
    def normalize(text: str) -> str:
        if not text:
            return text
        # Normalize unicode
        import unicodedata
        text = unicodedata.normalize("NFKC", text)
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Remove zero-width chars
        text = re.sub(r'[\u200b\u200c\u200d\ufeff]', '', text)
        return text


class PIIRedactor:
    """Detects and redacts PII patterns common in Indian government data."""

    PATTERNS = {
        "aadhaar": (r'\b\d{4}\s?\d{4}\s?\d{4}\b', "[AADHAAR_REDACTED]"),
        "phone": (r'\b(?:\+91[\s-]?)?[6-9]\d{9}\b', "[PHONE_REDACTED]"),
        "email": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[EMAIL_REDACTED]"),
        "pan": (r'\b[A-Z]{5}\d{4}[A-Z]\b', "[PAN_REDACTED]"),
        "bank_account": (r'\b\d{9,18}\b', None),  # Too broad for auto-redact, just detect
    }

    @classmethod
    def detect(cls, text: str) -> Dict[str, bool]:
        found = {}
        for name, (pattern, _) in cls.PATTERNS.items():
            found[name] = bool(re.search(pattern, text))
        return found

    @classmethod
    def redact(cls, text: str) -> Tuple[str, bool]:
        redacted = False
        result = text
        for name, (pattern, replacement) in cls.PATTERNS.items():
            if replacement:
                new_text = re.sub(pattern, replacement, result)
                if new_text != result:
                    redacted = True
                    result = new_text
        return result, redacted

    @classmethod
    def has_pii(cls, text: str) -> bool:
        for name, (pattern, _) in cls.PATTERNS.items():
            if name == "bank_account":
                continue  # Skip overly broad pattern
            if re.search(pattern, text):
                return True
        return False


class Deduplicator:
    """Detects exact and near-duplicate records."""

    @staticmethod
    def content_hash(text: str) -> str:
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()[:16]

    @classmethod
    def find_duplicates(cls, records: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        seen_hashes = {}
        unique = []
        duplicates = []

        for record in records:
            text = record.get("text", "")
            h = cls.content_hash(text)
            if h in seen_hashes:
                record["duplicate_group_id"] = h
                record["is_duplicate"] = True
                duplicates.append(record)
            else:
                seen_hashes[h] = True
                record["is_duplicate"] = False
                unique.append(record)

        return unique, duplicates


class IngestionPipeline:
    """Full ingestion pipeline: validate → normalize → PII → dedup → output."""

    def __init__(self):
        self.validator = TextValidator()
        self.normalizer = TextNormalizer()
        self.pii_redactor = PIIRedactor()
        self.deduplicator = Deduplicator()

    def process_records(self, records: List[Dict]) -> Dict:
        valid_records = []
        rejected = []

        # Step 1: Validate
        for record in records:
            ok, reason = self.validator.validate(record)
            if ok:
                valid_records.append(record)
            else:
                record["rejection_reason"] = reason
                rejected.append(record)

        # Step 2: Normalize
        for record in valid_records:
            record["normalized_text"] = self.normalizer.normalize(record.get("text", ""))

        # Step 3: PII Detection + Redaction
        for record in valid_records:
            text = record.get("text", "")
            record["pii_detected"] = self.pii_redactor.has_pii(text)
            if record["pii_detected"]:
                record["normalized_text"], record["pii_redacted"] = self.pii_redactor.redact(
                    record.get("normalized_text", text)
                )
            else:
                record["pii_redacted"] = False

        # Step 4: Deduplication
        unique, duplicates = self.deduplicator.find_duplicates(valid_records)

        return {
            "valid_records": unique,
            "duplicate_records": duplicates,
            "rejected_records": rejected,
            "stats": {
                "total_input": len(records),
                "valid": len(unique),
                "duplicates": len(duplicates),
                "rejected": len(rejected),
            }
        }

    def process_csv_content(self, content: str, column_mapping: Optional[Dict] = None) -> Dict:
        """Process CSV content string through the pipeline."""
        reader = csv.DictReader(io.StringIO(content))
        records = []

        # Auto-detect text column
        text_column = None
        possible_text_cols = ["text", "query", "question", "original_text", "content", "message"]

        for row in reader:
            if text_column is None:
                for col in possible_text_cols:
                    if col in row:
                        text_column = col
                        break
                if text_column is None and row:
                    text_column = list(row.keys())[0]

            record = {
                "text": row.get(text_column, ""),
                "scheme_name": row.get("scheme_name") or row.get("scheme") or row.get("Scheme Name"),
                "intent": row.get("intent") or row.get("Intent"),
                "awareness_gap": row.get("awareness_gap") or row.get("gap") or row.get("Awareness Gap"),
                "gap_type": row.get("gap_type") or row.get("Gap Type"),
                "state": row.get("state") or row.get("State"),
                "district": row.get("district") or row.get("District"),
                "source_name": row.get("source_name") or row.get("source") or row.get("Source"),
                "source_type": row.get("source_type") or row.get("Source Type"),
                "source_url": row.get("source_url") or row.get("url") or row.get("URL"),
                "confidence": row.get("confidence") or row.get("Confidence"),
                "notes": row.get("notes") or row.get("Notes"),
                "split": row.get("split") or row.get("Split"),
                "language": row.get("language") or row.get("Language"),
            }

            # Apply column mapping overrides
            if column_mapping:
                for target, source in column_mapping.items():
                    if source in row:
                        record[target] = row[source]

            records.append(record)

        return self.process_records(records)
