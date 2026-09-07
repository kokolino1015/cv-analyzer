from contextlib import contextmanager
from fastapi import HTTPException

import anthropic
import httpx

from models import AnalyzeRequest, MatchRequest


def require_inputs(req: AnalyzeRequest) -> None:
    if not req.cv_text.strip() or not req.job_listing.strip():
        raise HTTPException(status_code=400, detail="Both cv_text and job_listing are required")


def require_inputs_cv(req: MatchRequest) -> None:
    if not req.cv_text.strip():
        raise HTTPException(status_code=400, detail="Cv_text is required")


@contextmanager
def translate_provider_errors():
    try:
        yield
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama answered with an error: {e}")
