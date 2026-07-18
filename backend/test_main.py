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