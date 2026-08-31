from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.api.sessions import SESSIONS
from backend.app.agent.state import CustomerServiceState
from backend.app.agent.contracts import QuoteContext


def _quoted_state(session_id: str, customer_id: str) -> CustomerServiceState:
    state = CustomerServiceState(session_id=session_id, customer_id=customer_id)
    state.quote_context = QuoteContext(items=[{"name": f"{customer_id}商品", "quantity": 1, "subtotal": 10}], subtotal=10, total=10, delivery_mode="PICKUP")
    return state


def test_confirmation_is_scoped_to_the_customer_session():
    client = TestClient(app)
    first = _quoted_state("multi-a", "CUS001")
    second = _quoted_state("multi-b", "CUS002")
    SESSIONS[first.session_id] = first
    SESSIONS[second.session_id] = second
    try:
        response = client.post("/api/v1/sessions/multi-a/confirmations", params={"customer_id": "CUS001", "confirmed": True})
        assert response.status_code == 200
        assert response.json()["order_summary"]["status"] == "CONFIRMED"
        assert SESSIONS["multi-b"].known_facts.get("order_confirmation_status") is None
        assert client.post("/api/v1/sessions/multi-a/confirmations", params={"customer_id": "CUS002", "confirmed": True}).status_code == 403
    finally:
        SESSIONS.pop("multi-a", None)
        SESSIONS.pop("multi-b", None)
