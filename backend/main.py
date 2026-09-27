import os
import asyncio

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from pypdf import PdfReader

from errors import require_inputs, translate_provider_errors, translate_retrieval_errors
from models import AnalyzeRequest, StructuredAnalysis, AnalyzeResponse, UploadResponse, MatchRequest
from analysis import analyze_one
from retrieval import search
from providers.anthropic_provider import call_anthropic, call_anthropic_stream, call_anthropic_structured_stream
from providers.ollama_provider import call_ollama, call_ollama_stream, call_ollama_structured_stream

load_dotenv()

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="CV Analyzer")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    require_inputs(req)
    with translate_provider_errors():
        if req.provider == "anthropic":
            message = call_anthropic(req)
            text = message.content[0].text
        else:
            response = await call_ollama(req)
            text = response["message"]["content"]
    return AnalyzeResponse(analysis=text)


@app.post("/analyze_structured", response_model=StructuredAnalysis)
async def analyze_structured(req: AnalyzeRequest):
    require_inputs(req)
    return await analyze_one(req.cv_text, req.job_listing, req.provider)


@app.post("/analyze_stream")
async def analyze_stream(req: AnalyzeRequest):
    require_inputs(req)
    if req.provider == "anthropic":
        gen = call_anthropic_stream(req)
    else:
        gen = call_ollama_stream(req)
    return StreamingResponse(gen, media_type="text/plain")


@app.post("/analyze_structured_stream")
async def analyze_structured_stream(req: AnalyzeRequest):
    require_inputs(req)
    if req.provider == "anthropic":
        gen = call_anthropic_structured_stream(req)
    else:
        gen = call_ollama_structured_stream(req)
    return StreamingResponse(gen, media_type="text/plain")


@app.post("/match")
async def match(req: MatchRequest):
    if not req.cv_text.strip():
        raise HTTPException(status_code=400, detail="cv_text is required")

    with translate_retrieval_errors():
        matches = search(req.cv_text, top_k=req.top_k)

    if not matches:
        return []

    analyses = await asyncio.gather(*[
        analyze_one(req.cv_text, listing_text, req.provider)
        for _company, _title, listing_text, _distance in matches
    ])

    return [
        {
            "company": company,
            "title": title,
            "distance": distance,
            "analysis": analysis,
        }
        for (company, title, _text, distance), analysis in zip(matches, analyses)
    ]


@app.post("/upload_cv", response_model=UploadResponse)
async def upload_cv(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    try:
        reader = PdfReader(file.file)
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception:
        raise HTTPException(status_code=400, detail="Could not read PDF, the file may be corrupted")
    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No text found, the PDF may be scanned images (OCR not supported)",
        )
    return UploadResponse(text=text)
