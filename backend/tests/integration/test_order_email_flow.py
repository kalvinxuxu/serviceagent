from fastapi.testclient import TestClient
from backend.app.main import app

def test_order_email_requires_confirmation_before_send():
    client = TestClient(app)
    response = client.post("/api/v1/order-emails", json={"email_id":"flow-001","sender":"buyer@example.test","subject":"订单","body":"原味贝果1个，明天送到公司"})
    draft_id = response.json()["draft_id"]
    reply = client.post(f"/api/v1/order-drafts/{draft_id}/check").json()["reply"]
    assert client.post(f"/api/v1/reply-drafts/{reply['reply_id']}/send").status_code == 409
    assert client.post(f"/api/v1/reply-drafts/{reply['reply_id']}/confirm", json={"draft_version":1,"confirmed_by":"op","idempotency_key":"flow-001-v1"}).status_code == 200
    assert client.post(f"/api/v1/reply-drafts/{reply['reply_id']}/send").json()["status"] == "SENT"
