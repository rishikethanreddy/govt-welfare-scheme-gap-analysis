"""
Analyze API — single text analysis endpoint.
"""

from fastapi import APIRouter
from backend.app.schemas.document import AnalyzeTextRequest, AnalyzeTextResponse
from backend.app.services.nlp import get_nlp_service

router = APIRouter(prefix="/api", tags=["Analysis"])


@router.post("/analyze", response_model=AnalyzeTextResponse)
def analyze_text(request: AnalyzeTextRequest):
    """
    Analyze a single text through the NLP pipeline.

    Returns scheme detection, intent classification, awareness gap detection,
    and supporting signals from actual model outputs.
    """
    nlp = get_nlp_service()
    result = nlp.analyze_text(request.text)
    return AnalyzeTextResponse(**result)
