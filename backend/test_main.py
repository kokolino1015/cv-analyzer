import httpx
import anthropic
import pytest
from fastapi.testclient import TestClient
import analysis

import main
from main import app
from models import AnalyzeRequest, StructuredAnalysis
from errors import require_inputs
from providers.ollama_provider import extract_json_object, ollama_payload

client = TestClient(app)

VALID_BODY = {"cv_text": "Python developer, 3 years.", "job_listing": "Looking for a Python developer."}


class FakeContentBlock:
    def __init__(self, text=None, input=None):
        self.text = text
        self.input = input


class FakeMessage:
    def __init__(self, content):
        self.content = content


def fake_request():
    return httpx.Request("POST", "https://api.example.com")


def raising_anthropic_error(*_args, **_kwargs):
    raise anthropic.APIError("boom", fake_request(), body=None)


def raising_ollama_unreachable(*_args, **_kwargs):
    raise httpx.RequestError("connection refused")


def raising_ollama_http_error(*_args, **_kwargs):
    request = fake_request()
    response = httpx.Response(500, request=request)
    raise httpx.HTTPStatusError("server error", request=request, response=response)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.parametrize("endpoint", [
    "/analyze", "/analyze_stream", "/analyze_structured", "/analyze_structured_stream",
])
@pytest.mark.parametrize("body", [
    {"cv_text": "", "job_listing": ""},
    {"cv_text": "", "job_listing": "Some job listing."},
    {"cv_text": "Some CV.", "job_listing": ""},
    {"cv_text": "   ", "job_listing": "Some job listing."},
])
def test_rejects_blank_input(endpoint, body):
    r = client.post(endpoint, json=body)
    assert r.status_code == 400


def test_require_inputs_passes_for_valid_request():
    require_inputs(AnalyzeRequest(cv_text="cv", job_listing="job"))


def test_analyze_anthropic_success(monkeypatch):
    monkeypatch.setattr(main, "call_anthropic", lambda req: FakeMessage([FakeContentBlock(text="Good match.")]))
    r = client.post("/analyze", json={**VALID_BODY, "provider": "anthropic"})
    assert r.status_code == 200
    assert r.json() == {"analysis": "Good match."}


async def fake_call_ollama(_req):
    return {"message": {"content": "Decent match."}}


def test_analyze_ollama_success(monkeypatch):
    monkeypatch.setattr(main, "call_ollama", fake_call_ollama)
    r = client.post("/analyze", json={**VALID_BODY, "provider": "ollama"})
    assert r.status_code == 200
    assert r.json() == {"analysis": "Decent match."}


def test_analyze_anthropic_error_maps_to_502(monkeypatch):
    monkeypatch.setattr(main, "call_anthropic", raising_anthropic_error)
    r = client.post("/analyze", json={**VALID_BODY, "provider": "anthropic"})
    assert r.status_code == 502


def test_analyze_ollama_unreachable_maps_to_503(monkeypatch):
    monkeypatch.setattr(main, "call_ollama", raising_ollama_unreachable)
    r = client.post("/analyze", json={**VALID_BODY, "provider": "ollama"})
    assert r.status_code == 503


def test_analyze_ollama_http_error_maps_to_502(monkeypatch):
    monkeypatch.setattr(main, "call_ollama", raising_ollama_http_error)
    r = client.post("/analyze", json={**VALID_BODY, "provider": "ollama"})
    assert r.status_code == 502


STRUCTURED_RESULT = {"score": 85, "matched": ["Python"], "missing": ["AWS"], "suggestions": ["Learn AWS"]}


def test_analyze_structured_anthropic_success(monkeypatch):
    monkeypatch.setattr(
        analysis, "call_anthropic_structured",
        lambda req: FakeMessage([FakeContentBlock(input=STRUCTURED_RESULT)]),
    )
    r = client.post("/analyze_structured", json={**VALID_BODY, "provider": "anthropic"})
    assert r.status_code == 200
    assert r.json() == STRUCTURED_RESULT


async def fake_call_ollama_structured(_req):
    return {"message": {"content": '```json\n{"score": 85, "matched": ["Python"], '
                                    '"missing": ["AWS"], "suggestions": ["Learn AWS"]}\n```'}}


def test_analyze_structured_ollama_success_extracts_json_from_prose(monkeypatch):
    monkeypatch.setattr(analysis, "call_ollama_structured", fake_call_ollama_structured)
    r = client.post("/analyze_structured", json={**VALID_BODY, "provider": "ollama"})
    assert r.status_code == 200
    assert r.json() == STRUCTURED_RESULT


async def fake_call_ollama_structured_no_json(_req):
    return {"message": {"content": "Sorry, I can't help with that."}}


def test_analyze_structured_ollama_no_json_maps_to_502(monkeypatch):
    monkeypatch.setattr(analysis, "call_ollama_structured", fake_call_ollama_structured_no_json)
    r = client.post("/analyze_structured", json={**VALID_BODY, "provider": "ollama"})
    assert r.status_code == 502


async def fake_call_ollama_structured_malformed_json(_req):
    return {"message": {"content": '{"score": 85, "matched": [Python]}'}}


def test_analyze_structured_ollama_malformed_json_maps_to_502(monkeypatch):
    monkeypatch.setattr(analysis, "call_ollama_structured", fake_call_ollama_structured_malformed_json)
    r = client.post("/analyze_structured", json={**VALID_BODY, "provider": "ollama"})
    assert r.status_code == 502


def test_analyze_structured_fails_validation_maps_to_502(monkeypatch):
    bad_result = {"score": 150, "matched": [], "missing": [], "suggestions": []}
    monkeypatch.setattr(
        analysis, "call_anthropic_structured",
        lambda req: FakeMessage([FakeContentBlock(input=bad_result)]),
    )
    r = client.post("/analyze_structured", json={**VALID_BODY, "provider": "anthropic"})
    assert r.status_code == 502


async def fake_text_stream(_req):
    for chunk in ("Hello ", "there."):
        yield chunk


def test_analyze_stream_returns_concatenated_chunks(monkeypatch):
    monkeypatch.setattr(main, "call_anthropic_stream", fake_text_stream)
    r = client.post("/analyze_stream", json={**VALID_BODY, "provider": "anthropic"})
    assert r.status_code == 200
    assert r.text == "Hello there."


async def fake_structured_stream(_req):
    for chunk in ('{"score": 90, ', '"matched": ["Python"], "missing": [], "suggestions": []}'):
        yield chunk


def test_analyze_structured_stream_returns_concatenated_chunks(monkeypatch):
    monkeypatch.setattr(main, "call_ollama_structured_stream", fake_structured_stream)
    r = client.post("/analyze_structured_stream", json={**VALID_BODY, "provider": "ollama"})
    assert r.status_code == 200
    assert r.text == '{"score": 90, "matched": ["Python"], "missing": [], "suggestions": []}'


def test_upload_rejects_non_pdf():
    r = client.post("/upload_cv", files={"file": ("cv.txt", b"hello", "text/plain")})
    assert r.status_code == 400


class FakePage:
    def __init__(self, text):
        self._text = text

    def extract_text(self):
        return self._text


class FakePdfReader:
    def __init__(self, _file):
        self.pages = [FakePage("Experienced Python developer.")]


def test_upload_cv_success(monkeypatch):
    monkeypatch.setattr(main, "PdfReader", FakePdfReader)
    r = client.post("/upload_cv", files={"file": ("cv.pdf", b"%PDF-1.4 fake", "application/pdf")})
    assert r.status_code == 200
    assert r.json() == {"text": "Experienced Python developer."}


class EmptyPdfReader:
    def __init__(self, _file):
        self.pages = [FakePage(""), FakePage(None)]


def test_upload_cv_scanned_pdf_has_no_extractable_text(monkeypatch):
    monkeypatch.setattr(main, "PdfReader", EmptyPdfReader)
    r = client.post("/upload_cv", files={"file": ("cv.pdf", b"%PDF-1.4 fake", "application/pdf")})
    assert r.status_code == 400


class BrokenPdfReader:
    def __init__(self, _file):
        raise ValueError("not a PDF")


def test_upload_cv_corrupted_file(monkeypatch):
    monkeypatch.setattr(main, "PdfReader", BrokenPdfReader)
    r = client.post("/upload_cv", files={"file": ("cv.pdf", b"garbage", "application/pdf")})
    assert r.status_code == 400


def test_extract_json_object_pulls_json_out_of_surrounding_prose():
    raw = 'Sure, here you go:\n```json\n{"score": 42}\n```\nHope that helps!'
    assert extract_json_object(raw) == {"score": 42}


def test_extract_json_object_raises_when_no_braces_present():
    with pytest.raises(Exception):
        extract_json_object("no json here")


def test_ollama_payload_defaults():
    payload = ollama_payload("hello")
    assert payload["stream"] is False
    assert "format" not in payload
    assert "options" not in payload
    assert payload["messages"] == [{"role": "user", "content": "hello"}]


def test_ollama_payload_structured_adds_format_schema():
    payload = ollama_payload("hello", structured=True)
    assert payload["format"] == StructuredAnalysis.model_json_schema()


def test_ollama_payload_with_temperature_sets_options():
    payload = ollama_payload("hello", stream=True, temperature=0.1)
    assert payload["stream"] is True
    assert payload["options"] == {"temperature": 0.1}
