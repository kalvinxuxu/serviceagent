from fastapi.testclient import TestClient
from backend.app.main import app

def test_confirmation_and_handoff_context():
    client=TestClient(app)
    sid=client.post("/api/v1/sessions", json={"customer_id":"CUS001"}).json()["session_id"]
    client.post(f"/api/v1/sessions/{sid}/messages", json={"message":"我昨天买的东西想退"})
    client.post(f"/api/v1/sessions/{sid}/messages", json={"message":"确认退货"})
    response=client.post(f"/api/v1/sessions/{sid}/confirmations", params={"confirmed":True})
    assert response.status_code == 200
    context=client.get(f"/api/v1/sessions/{sid}/handoff")
    assert context.status_code == 200
