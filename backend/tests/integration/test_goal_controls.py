from fastapi.testclient import TestClient

from backend.app.main import app


def test_goal_can_pause_resume_and_end():
    client = TestClient(app)
    sid = client.post("/api/v1/sessions", json={}).json()["session_id"]
    assert client.post(f"/api/v1/sessions/{sid}/goals/pause", json={"reason": "换个问题"}).json()["status"] == "WAITING_USER"
    assert client.post(f"/api/v1/sessions/{sid}/goals/resume").json()["status"] == "IN_PROGRESS"
    assert client.post(f"/api/v1/sessions/{sid}/goals/end", json={"reason": "客户结束咨询"}).json()["status"] == "RESOLVED"
    state = client.get(f"/api/v1/sessions/{sid}").json()
    assert state["known_facts"]["goal_ended"] is True
