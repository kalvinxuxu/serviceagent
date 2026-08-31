from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.db.models.trace import HumanHandoff
from backend.app.db.session import SessionLocal


def test_handoff_persists_required_context_fields():
    state = CustomerServiceState(session_id="ses_required_handoff", customer_id="CUS001")
    run_turn(state, "请转人工")
    with SessionLocal() as db:
        handoff = db.query(HumanHandoff).filter_by(session_id=state.session_id).order_by(HumanHandoff.id.desc()).first()
    assert handoff is not None
    assert handoff.reason == "HUMAN_REQUEST_OR_HIGH_RISK"
    assert handoff.original_request == "请转人工"
    assert isinstance(handoff.known_facts, dict)
    assert handoff.completed_steps
    assert isinstance(handoff.pending_items, list)


def test_admin_entry_can_maintain_catalog_and_boundaries():
    client = TestClient(app)
    response = client.put("/api/v1/admin/inventory/SKU001", json={"stock": 4})
    assert response.status_code == 200
    assert response.json()["data"]["on_hand"] == 4
    assert response.json()["data"]["available_quantity"] == 4
    response = client.put("/api/v1/admin/recommendation-constraints", json={"max_results": 2})
    assert response.status_code == 200
    assert response.json()["max_results"] == 2
    audit = client.get("/api/v1/admin/audit", params={"key": "recommendation_constraints"})
    assert audit.status_code == 200
    assert audit.json()["items"]


def test_admin_entry_can_maintain_sales_policy_and_audit():
    client = TestClient(app)
    response = client.put("/api/v1/admin/sales-policy", json={
        "member_discount_rate": 0.95,
        "threshold_discounts": [
            {"threshold": 30, "discount": 3, "label": "满30减3"},
            {"threshold": 50, "discount": 5, "label": "满50减5"},
        ],
        "free_shipping_threshold": 80,
        "shipping_fee": 6,
    })
    assert response.status_code == 200
    assert response.json()["free_shipping_threshold"] == 80
    audit = client.get("/api/v1/admin/audit", params={"key": "sales_policy"})
    assert audit.status_code == 200
    assert audit.json()["items"]
