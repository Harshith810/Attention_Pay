from pydantic import BaseModel, Field


class URLAnalysisRequest(BaseModel):
    url: str = Field(..., min_length=1)


class URLAnalysisResponse(BaseModel):
    prediction: str
    confidence: float
    phishing_probability: float
    legitimate_probability: float
    blocked: bool