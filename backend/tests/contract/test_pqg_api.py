from fastapi.testclient import TestClient
from backend.app.main import app


def test_pqg_api_contract():
    client = TestClient(app)
    session_id = client.post("/api/v1/sessions", json={"customer_id": "CUS001", "group_member_ids": ["CUS001"]}).json()["session_id"]
    chat = client.post(f"/api/v1/sessions/{session_id}/messages", headers={"X-Session-Owner": "CUS001"}, data={"message": "全麦吐司库存", "customer_id": "CUS001"})
    reply = chat.json()["message"]["content"]
    response = client.post(f"/api/v1/sessions/{session_id}/proactive-questions", headers={"X-Session-Owner": "CUS001"}, json={"session_id": session_id, "assistant_message_id": "m-contract", "context": "ignored-client-context", "reply": reply})
    body = response.json()
    assert response.status_code == 200
    assert body["schema_version"] == "pqg.v1"
    assert body["status"] in {"READY", "EMPTY", "DEGRADED"}
    assert len(body["questions"]) <= 3
