from fastapi.testclient import TestClient
from backend.app.main import app

def test_quickstart_scenario():
    client=TestClient(app); sid=client.post("/api/v1/sessions",json={}).json()["session_id"]
    response=client.post(f"/api/v1/sessions/{sid}/messages",json={"message":"全麦吐司还有货吗？"})
    assert response.json()["status"] == "IN_PROGRESS"
    assert client.get(f"/api/v1/sessions/{sid}/trace").json()["steps"]
