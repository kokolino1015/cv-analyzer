import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
import anthropic
from typing import Literal

load_dotenv()

app = FastAPI(title="CV Analyzer")
client = anthropic.Anthropic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
