from fastapi.testclient import TestClient
from backend.app.main import app

def test_catalog_conversation_returns_observation():
    c=TestClient(app); sid=c.post("/api/v1/sessions",json={}).json()["session_id"]
    result=c.post(f"/api/v1/sessions/{sid}/messages",json={"message":"低糖贝果还有货吗？"}).json()
    assert result["inspector"]["reason_code"] == "INVENTORY_REQUIRED"
