import json
import os

import httpx
from fastapi import HTTPException

from models import StructuredAnalysis, AnalyzeRequest
from prompts import task_prompt, json_prompt

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/chat")
OLLAMA_MODEL = "gemma3:27b"

def extract_json_object(raw: str) -> dict:
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise HTTPException(status_code=502, detail=f"No JSON in model output: {raw[:200]!r}")
    return json.loads(raw[start:end + 1])

def ollama_payload(content: str, *, stream: bool = False, structured: bool = False,
                    temperature: float | None = None) -> dict:
    payload = {
        "model": OLLAMA_MODEL,
        "messages": [{"role": "user", "content": content}],
        "stream": stream,
    }
    if structured:
        payload["format"] = StructuredAnalysis.model_json_schema()
    if temperature is not None:
        payload["options"] = {"temperature": temperature}
    return payload

async def ollama_chat(payload: dict) -> dict:
    async with httpx.AsyncClient() as ollama:
        response = await ollama.post(OLLAMA_URL, json=payload, timeout=120.0)
    response.raise_for_status()
    return response.json()


async def ollama_stream(payload: dict):
    async with httpx.AsyncClient() as ollama:
        async with ollama.stream("POST", OLLAMA_URL, json=payload, timeout=120.0) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    yield json.loads(line)["message"]["content"]


async def call_ollama(prompt: AnalyzeRequest) -> dict:
    return await ollama_chat(ollama_payload(task_prompt(prompt)))


async def call_ollama_structured(prompt: AnalyzeRequest) -> dict:
    return await ollama_chat(ollama_payload(json_prompt(prompt), structured=True))


async def call_ollama_stream(prompt: AnalyzeRequest):
    try:
        async for chunk in ollama_stream(ollama_payload(task_prompt(prompt), stream=True, temperature=0.1)):
            yield chunk
    except httpx.HTTPError as e:
        yield f"\n\n[ERROR: {e}]"


async def call_ollama_structured_stream(prompt: AnalyzeRequest):
    try:
        async for chunk in ollama_stream(ollama_payload(json_prompt(prompt), stream=True, structured=True)):
            yield chunk
    except httpx.HTTPError as e:
        yield f"\n\n[ERROR: {e}]"