from pydantic import BaseModel, Field
from typing import Literal


class StructuredAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    matched: list[str]
    missing: list[str]
    suggestions: list[str]


class UploadResponse(BaseModel):
    text: str


class AnalyzeRequest(BaseModel):
    cv_text: str
    job_listing: str
    provider: Literal["anthropic", "ollama"] = "anthropic"


class AnalyzeResponse(BaseModel):
    analysis: str

class MatchRequest(BaseModel):
    cv_text: str
    provider: Literal["anthropic", "ollama"] = "anthropic"
    top_k: int = Field(default=3, ge=1, le=10)