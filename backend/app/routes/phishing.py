from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.schemas.phishing import (
    URLAnalysisRequest,
    URLAnalysisResponse,
)
from backend.app.services.bert_service import BERTService
from backend.app.services.stage_flow_service import (
    stage_flow_service,
)


router = APIRouter(
    prefix="/api/v1/analyze",
    tags=["Phishing Detection"],
)

bert_service = BERTService()


@router.post(
    "/url",
    response_model=URLAnalysisResponse,
)
def analyze_url(
    request: URLAnalysisRequest,
    db: Session = Depends(get_db),
):
    result = bert_service.predict(
        request.url
    )

    blocked = (
        result["prediction"]
        == "PHISHING"
    )

    stage2_access_token = None
    explanation_source = None
    explanation = None

    if blocked:
        explanation_source = "bert_url"
        explanation = bert_service.explain(
            request.url
        )
    else:
        stage2_access_token = (
            stage_flow_service
            .create_stage2_access(db)
    )

    return {
        **result,
        "blocked": blocked,
        "explanation_source": explanation_source,
        "explanation": explanation,
        "stage2_access_token": (
            stage2_access_token
        ),
    }
