from fastapi.testclient import TestClient
from backend.app.main import app
def test_duplicate_email_is_idempotent():
    c=TestClient(app); body={'email_id':'dup-001','sender':'a@test','subject':'order','body':'SKU022 1 piece, deliver tomorrow to company'}
    first=c.post('/api/v1/order-emails',json=body).json(); second=c.post('/api/v1/order-emails',json=body).json()
    assert first['draft_id']==second['draft_id'] and second['status']=='DUPLICATE'
