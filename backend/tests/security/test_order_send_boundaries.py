from fastapi.testclient import TestClient
from backend.app.main import app
def test_unconfirmed_send_is_blocked():
    c=TestClient(app); r=c.post('/api/v1/order-emails',json={'email_id':'security-001','sender':'a@test','subject':'order','body':'SKU022 1 piece, deliver tomorrow to company'}).json(); reply=c.post(f"/api/v1/order-drafts/{r['draft_id']}/check").json()['reply']; assert c.post(f"/api/v1/reply-drafts/{reply['reply_id']}/send").status_code == 409
