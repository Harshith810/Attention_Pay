from typing import List, Optional

from pydantic import BaseModel, Field


class URLAnalysisRequest(BaseModel):
    url: str = Field(..., min_length=1)


class BERTTokenExplanation(BaseModel):
    token: str
    importance: float
    positions: List[int]


class BERTURLExplanation(BaseModel):
    type: str
    summary: str
    suspicious_tokens: List[BERTTokenExplanation]
    attention: List[BERTTokenExplanation]


class URLAnalysisResponse(BaseModel):
    prediction: str
    confidence: float
    phishing_probability: float
    legitimate_probability: float
    blocked: bool
    explanation_source: Optional[str] = None
    explanation: Optional[BERTURLExplanation] = None
    stage2_access_token: Optional[str] = None
