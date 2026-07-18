# CV Analyzer

AI-powered tool that compares a CV against a job listing and returns a match analysis — matched requirements, gaps, a match score, and concrete suggestions to improve the fit.

Built as a fullstack project: **FastAPI** backend calling the **Anthropic API**, **React + TypeScript** frontend, containerized with **Docker**, tested with **pytest**, CI via **GitHub Actions**.

## Tech stack

- **Backend:** Python, FastAPI, Pydantic, Anthropic SDK
- **Frontend:** React, TypeScript, Vite
- **Infra:** Docker, GitHub Actions (CI), pytest

## Running locally

### Backend
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
echo "ANTHROPIC_API_KEY=your-key-here" > .env
uvicorn main:app --reload
```
API docs at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
App at http://localhost:5173

### Docker (backend)
```bash
cd backend
docker build -t cv-analyzer .
docker run -p 8000:8000 --env-file .env cv-analyzer
```

## API

- `GET /health` — liveness check
- `POST /analyze` — `{ "cv_text": "...", "job_listing": "..." }` → `{ "analysis": "..." }`

## What I'd add next

- Structured JSON output (score, matched/missing lists) rendered as a proper UI
- PDF upload for the CV (text extraction server-side)
- Streaming responses (SSE) for token-by-token output
- Rate limiting and a deployed demo