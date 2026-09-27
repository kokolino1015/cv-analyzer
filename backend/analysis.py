import asyncio
import json

from fastapi import HTTPException

from errors import translate_provider_errors
from models import StructuredAnalysis, AnalyzeRequest
from providers.anthropic_provider import call_anthropic_structured, call_anthropic
from providers.ollama_provider import call_ollama_structured, extract_json_object, call_ollama


async def analyze_one(cv_text: str, listing_text: str, provider: str) -> StructuredAnalysis:
    req = AnalyzeRequest(cv_text=cv_text, job_listing=listing_text, provider=provider)
    with translate_provider_errors():
        try:
            if provider == "anthropic":
                message = await asyncio.to_thread(call_anthropic_structured, req)
                parsed = message.content[0].input
            else:
                response = await call_ollama_structured(req)
                parsed = extract_json_object(response["message"]["content"])
        except json.JSONDecodeError as e:
            raise HTTPException(status_code=502, detail=f"Malformed model output: {e}")

    try:
        return StructuredAnalysis(**parsed)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Model output failed validation: {e}")
