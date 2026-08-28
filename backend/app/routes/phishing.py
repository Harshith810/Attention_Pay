from fastapi import APIRouter

from backend.app.schemas.phishing import (
    URLAnalysisRequest,
    URLAnalysisResponse,
)
from backend.app.services.bert_service import BERTService


router = APIRouter(
    prefix="/api/v1/analyze",
    tags=["Phishing Detection"],
)

bert_service = BERTService()


@router.post("/url", response_model=URLAnalysisResponse)
def analyze_url(request: URLAnalysisRequest):
    result = bert_service.predict(request.url)

    blocked = result["prediction"] == "PHISHING"

    return {
        **result,
        "blocked": blocked,
    }