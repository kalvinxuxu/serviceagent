from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.agent.contracts import QuoteContext
from backend.app.db.seed import load_products_from_seed


def test_member_discount_question_recalculates_existing_quote():
    state = CustomerServiceState(session_id="membership_route_test", customer_id="CUS001")
    load_products_from_seed()
    state.quote_context = QuoteContext(items=[{"product_id": "SKU009", "name": "芝士贝果", "quantity": 2, "unit_price": 13}])
    state.known_facts["selected_products"] = state.quote_context.items
    state, reply, trace = run_turn(state, "\u6211\u662f\u4f1a\u5458\uff0c\u521a\u624d\u8fd9\u4e9b\u4e1c\u897f\u6709\u6ca1\u6709\u4f1a\u5458\u4f18\u60e0\uff1f")
    assert trace["goal"]["type"] == "MEMBERSHIP_PRICING"
    assert trace["next_action"]["tool_name"] == "calculate_order_quote"
    assert "\u4f1a\u5458" in reply or "\u4f18\u60e0" in reply
    assert state.quote_context is not None
