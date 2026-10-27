"""Run with:  pytest -q   (from backend/)"""
import os

os.environ["DATABASE_URL"] = "sqlite:///./test_fakenews.db"

from fastapi.testclient import TestClient  # noqa: E402

from main import app  # noqa: E402

client = TestClient(app)

FAKE = "SHOCKING!!! Doctors HATE this one weird trick, big pharma is hiding the secret, share this with 10 people now!!!"
REAL = "The central bank held interest rates steady on Wednesday, according to a statement from the governor, officials said."


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_fake_vs_real():
    f = client.post("/api/analyze", json={"text": FAKE}).json()
    r = client.post("/api/analyze", json={"text": REAL}).json()
    assert f["fake_probability"] > r["fake_probability"]
    assert f["verdict"] == "Likely Fake"
    assert r["verdict"] == "Likely Real"


def test_validation():
    assert client.post("/api/analyze", json={}).status_code == 422
    assert client.post("/api/analyze", json={"text": "hi"}).status_code == 422


def test_history_feedback_stats_delete():
    a = client.post("/api/analyze", json={"text": FAKE}).json()
    fb = client.post(f"/api/feedback/{a['id']}", json={"label": "fake"})
    assert fb.status_code == 200 and fb.json()["user_label"] == "fake"
    assert client.post(f"/api/feedback/{a['id']}", json={"label": "maybe"}).status_code == 422
    assert len(client.get("/api/history").json()) >= 1
    assert client.get("/api/stats").json()["total"] >= 1
    assert client.delete(f"/api/history/{a['id']}").status_code == 204
    assert client.get(f"/api/analysis/{a['id']}").status_code == 404


def test_ssrf_blocked():
    r = client.post("/api/analyze", json={"url": "http://127.0.0.1:8000/"})
    assert r.status_code == 422