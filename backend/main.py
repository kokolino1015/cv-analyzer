import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
import anthropic
from typing import Literal
import json
from fastapi.responses import StreamingResponse

load_dotenv()

app = FastAPI(title="CV Analyzer")
client = anthropic.Anthropic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    provider: Literal["anthropic", "ollama"] = "ollama"


class AnalyzeResponse(BaseModel):
    analysis: str


@app.get("/health")
def health():
    return {"status": "ok"}


def call_anthropic(prompt: AnalyzeRequest):
    return client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": (
                "Compare this CV against this job listing.\n"
                "Return: 1) matched requirements, 2) missing requirements, "
                "3) partially matched with explanation, 4) match score 0-100, "
                "5) two concrete suggestions to improve the match.\n\n"
                f"CV:\n{prompt.cv_text}\n\nJOB LISTING:\n{prompt.job_listing}"
            ),
        }],
    )


async def call_ollama(prompt: AnalyzeRequest):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "gemma3:27b",
        "messages": [{
            "role": "user",
            "content": (
                "Compare this CV against this job listing.\n"
                "Return: 1) matched requirements, 2) missing requirements, "
                "3) partially matched with explanation, 4) match score 0-100, "
                "5) two concrete suggestions to improve the match.\n\n"
                f"CV:\n{prompt.cv_text}\n\nJOB LISTING:\n{prompt.job_listing}"
            )}],
        "stream": False
    }

    async with httpx.AsyncClient() as ollama:
        response = await ollama.post(url, json=payload, timeout=120.0)
    response.raise_for_status()
    return response.json()


def call_anthropic_structured(prompt: AnalyzeRequest):
    return client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        temperature=0,
        tools=[{
            "name": "submit_analysis",
            "description": "Submit the CV-vs-listing analysis result",
            "input_schema": StructuredAnalysis.model_json_schema(),
        }],
        tool_choice={"type": "tool", "name": "submit_analysis"},
        messages=[{
            "role": "user",
            "content": (
                "Compare this CV against the job listing and submit the analysis.\n\n"
                f"CV:\n{prompt.cv_text}\n\nJOB LISTING:\n{prompt.job_listing}"
            ),
        }],
    )

async def call_ollama_structured(prompt: AnalyzeRequest):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "gemma3:27b",
        "messages": [{
            "role": "user",
            "content": (
                'Compare this CV against the job listing. Respond with ONLY a valid JSON object — no markdown, '
                'no code fences, no text before or after — in exactly this structure: {"score": <integer 0-100>, "matched": [<strings>], '
                '"missing": [<strings>], "suggestions": [<strings>]}. '
                f'CV:\n{prompt.cv_text}\n\nLISTING:\n{prompt.job_listing}'
            )}],
        "stream": False,
        "format": StructuredAnalysis.model_json_schema()
    }

    async with httpx.AsyncClient() as ollama:
        response = await ollama.post(url, json=payload, timeout=120.0)
    response.raise_for_status()
    return response.json()


async def call_anthropic_stream(prompt: AnalyzeRequest):
    try:
        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": (
                    "Compare this CV against this job listing.\n"
                    "Return: 1) matched requirements, 2) missing requirements, "
                    "3) partially matched with explanation, 4) match score 0-100, "
                    "5) two concrete suggestions to improve the match.\n\n"
                    f"CV:\n{prompt.cv_text}\n\nJOB LISTING:\n{prompt.job_listing}"
                ),
            }],
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"\n\n[ERROR: {e}]"


async def call_ollama_stream(prompt: AnalyzeRequest):
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": "qwen3-coder:30b",
        "messages": [{
            "role": "user",
            "content": (
                "Compare this CV against this job listing.\n"
                "Return: 1) matched requirements, 2) missing requirements, "
                "3) partially matched with explanation, 4) match score 0-100, "
                "5) two concrete suggestions to improve the match.\n\n"
                f"CV:\n{prompt.cv_text}\n\nJOB LISTING:\n{prompt.job_listing}"
            )}],
        "stream": True,
        "options": {
            "temperature": 0.1
        }
    }
    try:
        async with httpx.AsyncClient() as ollama:
            async with ollama.stream("POST", url, json=payload, timeout=120.0) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.strip():
                        result = json.loads(line)
                        yield result["message"]["content"]
    except httpx.HTTPError as e:
        yield f"\n\n[ERROR: {e}]"


@app.post("/analyze_stream")
async def analyze_stream(req: AnalyzeRequest):
    if not req.cv_text.strip() or not req.job_listing.strip():
        raise HTTPException(status_code=400, detail="Both cv_text and job_listing are required")

    if req.provider == "anthropic":
        response = call_anthropic_stream(req)
    else:
        response = call_ollama_stream(req)

    return StreamingResponse(response, media_type="text/plain")


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    if not req.cv_text.strip() or not req.job_listing.strip():
        raise HTTPException(status_code=400, detail="Both cv_text and job_listing are required")
    try:
        if req.provider == "anthropic":
            message = call_anthropic(req)
            text = message.content[0].text
        else:
            response = await call_ollama(req)
            text = response["message"]["content"]

        return AnalyzeResponse(analysis=text)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama answered with an error: {e}")


@app.post("/analyze_structured", response_model=StructuredAnalysis)
async def analyze_structured(req: AnalyzeRequest):
    if not req.cv_text.strip() or not req.job_listing.strip():
        raise HTTPException(status_code=400, detail="Both cv_text and job_listing are required")
    try:
        if req.provider == "anthropic":
            message = call_anthropic_structured(req)
            parsed = message.content[0].input
        else:
            response = await call_ollama_structured(req)
            raw = response["message"]["content"]
            start, end = raw.find("{"), raw.rfind("}")
            if start == -1 or end == -1:
                raise HTTPException(status_code=502, detail=f"No JSON in model output: {raw[:200]!r}")
            parsed = json.loads(raw[start:end + 1])
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Ollama answered with an error: {e}")
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Malformed model output: {e}")

    try:
        return StructuredAnalysis(**parsed)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=f"Model output failed validation: {e}")

@app.post("/upload_cv", response_model=UploadResponse)
async def upload_cv(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    try:
        reader = PdfReader(file.file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read PDF — file may be corrupted")
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text found — the PDF may be scanned images (OCR not supported)",
        )
    return UploadResponse(text=text)
