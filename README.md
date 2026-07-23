# CV Analyzer

AI-powered tool that compares a CV against a job listing and returns a match analysis — a match score, matched and missing requirements, and concrete suggestions to improve the fit.

Built as a fullstack learning project with a focus on real LLM integration patterns: multi-provider support, schema-constrained structured output, and token-by-token streaming with live-assembling UI.

## Features

- **Multi-provider LLM backend** — Anthropic (Claude) via the official SDK, and local models via Ollama's native HTTP API (httpx), selectable per request
- **Four analysis modes** — plain text or structured output, each available streaming or non-streaming
- **Schema-constrained structured output** — Anthropic via forced tool use (`tool_choice` + `input_schema`), Ollama via the `format` JSON-schema parameter; both driven by a single Pydantic model that also validates the output server-side
- **Streaming structured output with a hand-rolled partial JSON parser** — the frontend parses incomplete JSON as it streams (stack-based bracket balancing with string-state tracking), so the score badge and requirement lists assemble live
- **PDF upload** — extracts CV text server-side (pypdf) with validation for non-PDFs, corrupt files, and scanned images
- **Layered error handling** — distinct status codes for client errors (400), upstream LLM failures (502), and provider unavailability (503); in-stream failures surface as error markers since headers are already sent

## Tech stack

- **Backend:** Python, FastAPI, Pydantic, httpx, Anthropic SDK, pypdf
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

For the Ollama provider, [Ollama](https://ollama.com) must be running locally with a pulled model (default: `gemma3:27b`).

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
- `POST /analyze` — full text analysis
- `POST /analyze_stream` — text analysis, streamed token by token
- `POST /analyze_structured` — validated JSON result (score, matched, missing, suggestions)
- `POST /analyze_structured_stream` — structured result streamed as partial JSON, parsed incrementally client-side
- `POST /upload_cv` — PDF upload, returns extracted text

All analyze endpoints accept `{ "cv_text": "...", "job_listing": "...", "provider": "anthropic" | "ollama" }`.

## Notes on the partial JSON parser

Streaming a JSON object token-by-token means the buffer is almost always invalid JSON mid-stream. The frontend repairs it on each chunk: a stack tracks open brackets, a flag tracks string state (so structural characters inside strings are ignored), dangling strings and separators are trimmed, open brackets are closed in LIFO order, and the result is parsed — falling back to the last valid parse on failure.

Hand-rolling this surfaced its real limits (incomplete trailing key-values fail the whole parse; truncation can desync the bracket stack). The robust production alternatives are a battle-tested partial-JSON library, or streaming NDJSON events so each field parses independently.

## What I'd add next

- NDJSON event streaming as the robust alternative to partial JSON parsing
- Swap the hand-rolled parser for `best-effort-json-parser` for edge cases (escapes, unicode)
- docker-compose for one-command startup of both services
- Deployment (rate-limited) with a hosted demo
- Async Anthropic client for fully non-blocking streaming