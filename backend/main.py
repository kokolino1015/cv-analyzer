from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import anthropic

load_dotenv()

app = FastAPI(title="CV Analyzer")
client = anthropic.Anthropic()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    cv_text: str
    job_listing: str

class AnalyzeResponse(BaseModel):
    analysis: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    if not req.cv_text.strip() or not req.job_listing.strip():
        raise HTTPException(status_code=400, detail="Both cv_text and job_listing are required")
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": (
                    "Compare this CV against this job listing.\n"
                    "Return: 1) matched requirements, 2) missing requirements, "
                    "3) partially matched with explanation, 4) match score 0-100, "
                    "5) two concrete suggestions to improve the match.\n\n"
                    f"CV:\n{req.cv_text}\n\nJOB LISTING:\n{req.job_listing}"
                ),
            }],
        )
        return AnalyzeResponse(analysis=message.content[0].text)
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")
