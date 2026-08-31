from fastapi.testclient import TestClient
from backend.app.main import app
def test_ingestion_contract():
    r = TestClient(app).post('/api/v1/order-emails', json={'email_id':'contract-001','sender':'a@test','subject':'order','body':'SKU022 1 piece, deliver tomorrow to company'})
    assert r.status_code == 200 and 'draft_id' in r.json()
