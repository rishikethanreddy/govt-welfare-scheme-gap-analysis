"""
NLP service — orchestrates scheme detection, intent classification,
awareness gap detection, and embedding generation.

Wraps the existing ML modules from ml/ (to be moved to backend/nlp/ later).
For Phase 1, this provides a clean API surface without requiring ML model loading.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NLPService:
    """
    Orchestrates the NLP pipeline. Currently provides a skeleton that
    returns stub results. Phase 6 will wire in the actual ML modules.
    """

    def __init__(self):
        self._scheme_detector = None
        self._intent_classifier = None
        self._gap_classifier = None
        self._text_encoder = None
        self._initialized = False

    @property
    def is_initialized(self) -> bool:
        return self._initialized

    def initialize(self):
        """
        Lazily load ML models. Called on first use, not at startup.
        This avoids blocking server startup with model loading.
        """
        if self._initialized:
            return

        try:
            from ml.preprocessing.text_cleaner import TextCleaner
            from ml.scheme_detection.detector import SchemeDetector
            from ml.intent.classifier import IntentClassifier
            from ml.awareness_gap.classifier import AwarenessGapClassifier

            self._text_cleaner = TextCleaner()
            self._scheme_detector = SchemeDetector()
            self._intent_classifier = IntentClassifier()
            self._gap_classifier = AwarenessGapClassifier()
            self._initialized = True
            logger.info("NLP pipeline initialized (rule-based models loaded)")
        except ImportError as e:
            logger.warning(f"ML modules not available: {e}. NLP analysis will return defaults.")
        except Exception as e:
            logger.error(f"Failed to initialize NLP pipeline: {e}")

    def analyze_text(self, text: str) -> dict:
        """
        Run the full NLP pipeline on a single text.
        Returns analysis results with actual model outputs.
        """
        if not self._initialized:
            self.initialize()

        result = {
            "text": text,
            "normalized_text": text,
            "scheme": None,
            "scheme_confidence": None,
            "scheme_matched_entities": [],
            "intent": None,
            "intent_confidence": None,
            "awareness_gap": None,
            "gap_confidence": None,
            "gap_type": None,
            "gap_type_confidence": None,
            "supporting_signals": [],
            "language": "en",
            "geography": None,
            "model_versions": {},
        }

        if not self._initialized:
            result["supporting_signals"].append({
                "signal": "NLP models not loaded",
                "detail": "ML modules are not available. Results are defaults.",
            })
            return result

        # 1. Text cleaning
        try:
            result["normalized_text"] = self._text_cleaner.clean_text(text)
        except Exception as e:
            logger.error(f"Text cleaning failed: {e}")

        # 2. Scheme detection
        try:
            scheme = self._scheme_detector.detect_scheme(text)
            result["scheme"] = scheme
            if scheme != "Other / Unknown":
                result["scheme_confidence"] = 0.9  # Rule-based = high confidence on match
                result["supporting_signals"].append({
                    "signal": "Scheme detected via keyword matching",
                    "detail": f"Matched scheme: {scheme}",
                })
        except Exception as e:
            logger.error(f"Scheme detection failed: {e}")

        # 3. Intent classification
        try:
            if self._intent_classifier and self._intent_classifier.model:
                intent, confidence = self._intent_classifier.predict(text)
                result["intent"] = intent
                result["intent_confidence"] = confidence
        except Exception as e:
            logger.error(f"Intent classification failed: {e}")

        # 4. Awareness gap detection
        try:
            if self._gap_classifier and self._gap_classifier.binary_model:
                gap_result = self._gap_classifier.predict(text)
                result["awareness_gap"] = gap_result.get("awareness_gap", "no")
                result["gap_confidence"] = gap_result.get("gap_confidence")
                result["gap_type"] = gap_result.get("gap_type", "none")
                result["gap_type_confidence"] = gap_result.get("type_confidence")
            else:
                # Fallback rule-based gap detection for Phase 1 / Testing
                text_lower = text.lower()
                is_question = "?" in text or any(text_lower.startswith(w) for w in ["how", "what", "where", "why", "who", "am i", "can i", "is it"])
                
                if is_question or "pending" in text_lower or "not received" in text_lower:
                    result["awareness_gap"] = "Yes"
                    result["gap_confidence"] = 0.8
                    if "eligible" in text_lower or "am i" in text_lower:
                        result["gap_type"] = "Eligibility Confusion"
                    elif "apply" in text_lower or "register" in text_lower or "status" in text_lower or "pending" in text_lower:
                        result["gap_type"] = "Application Process"
                    elif "premium" in text_lower or "rate" in text_lower:
                        result["gap_type"] = "Benefit Misconception"
                    else:
                        result["gap_type"] = "General Query"
                else:
                    result["awareness_gap"] = "No"
                    result["gap_type"] = "None"
        except Exception as e:
            logger.error(f"Awareness gap detection failed: {e}")

        return result

    def get_status(self) -> dict:
        """Return NLP pipeline status."""
        return {
            "initialized": self._initialized,
            "scheme_detector": self._scheme_detector is not None,
            "intent_classifier": self._intent_classifier is not None and (
                hasattr(self._intent_classifier, 'model') and self._intent_classifier.model is not None
            ) if self._intent_classifier else False,
            "gap_classifier": self._gap_classifier is not None and (
                hasattr(self._gap_classifier, 'binary_model') and self._gap_classifier.binary_model is not None
            ) if self._gap_classifier else False,
        }


# Singleton instance
_nlp_service: Optional[NLPService] = None


def get_nlp_service() -> NLPService:
    global _nlp_service
    if _nlp_service is None:
        _nlp_service = NLPService()
    return _nlp_service
