from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_analyze_rejects_empty_input():
    r = client.post("/analyze", json={"cv_text": "", "job_listing": ""})
    assert r.status_code == 400

def test_upload_rejects_non_pdf():
    r = client.post("/upload_cv", files={"file": ("cv.txt", b"hello", "text/plain")})
    assert r.status_code == 400