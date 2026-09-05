from fastapi.testclient import TestClient
from backend.app.main import app

def test_chat_api_round_trip():
    client=TestClient(app)
    session=client.post("/api/v1/sessions", json={"customer_id":"CUS001"}).json()["session_id"]
    response=client.post(f"/api/v1/sessions/{session}/messages", json={"message":"\u5168\u9ea6\u5410\u53f8\u8fd8\u6709\u8d27\u5417\uff1f"})
    assert response.status_code == 200
    assert response.json()["inspector"]["next_action"]["type"] == "TOOL_CALL"
