from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.sessions import SESSIONS


def test_session_can_be_reloaded_from_checkpoint():
    client = TestClient(app)
    sid = client.post("/api/v1/sessions", json={}).json()["session_id"]
    client.post(f"/api/v1/sessions/{sid}/messages", json={"message": "全麦吐司还有货吗？"})
    SESSIONS.pop(sid, None)
    restored = client.get(f"/api/v1/sessions/{sid}")
    assert restored.status_code == 200
    assert restored.json()["messages"]


def test_unknown_request_uses_structured_provider_path():
    client = TestClient(app)
    sid = client.post("/api/v1/sessions", json={}).json()["session_id"]
    response = client.post(f"/api/v1/sessions/{sid}/messages", json={"message": "我有个问题想咨询"})
    assert response.status_code == 200
    assert response.json()["inspector"]["next_action"]["type"] == "ASK_USER"
