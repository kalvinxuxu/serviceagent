from fastapi.testclient import TestClient

from backend.app.main import app


def test_session_api_shape_remains_legacy_compatible(monkeypatch):
    monkeypatch.setenv("AGENT_ARCHITECTURE", "legacy")
    client = TestClient(app)
    created = client.post("/api/v1/sessions", json={"customer_id": "CUS001"})
    assert created.status_code == 200
    session_id = created.json()["session_id"]
    response = client.post(f"/api/v1/sessions/{session_id}/messages", json={"message": "你好"})
    assert response.status_code == 200
    payload = response.json()
    assert {"session_id", "message", "status", "inspector"}.issubset(payload)
