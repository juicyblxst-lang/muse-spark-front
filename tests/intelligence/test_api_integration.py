from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_request_reaches_backend():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "muse-intelligence"}

def test_readiness_rejects_missing_database_configuration(monkeypatch):
    monkeypatch.delenv("MUSE_DATABASE_PATH", raising=False)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"

def test_private_routes_reject_or_report_unimplemented_without_fabrication():
    assert client.get("/api/v1/auth/me").status_code == 401
    assert client.get("/api/v1/dashboard").status_code == 501
    assert client.get("/api/v1/documents").status_code == 501
    assert client.post("/api/v1/documents/uploads").status_code == 501
    assert client.get("/api/v1/memories/forgotten").status_code == 501
