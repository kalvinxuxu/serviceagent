import os
from uuid import uuid4

from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed


load_products_from_seed()


def test_converged_atomic_inventory_query_uses_direct_decision():
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["AGENT_ARCHITECTURE"] = "converged"
    state, reply, trace = run_turn(CustomerServiceState(session_id=f"short-inventory-{uuid4().hex}"), "原味贝果有货吗")
    assert reply
    assert trace["next_action"]["tool_name"] == "check_inventory"
    assert trace["reason_code"] == "ATOMIC_INVENTORY_QUERY"
    assert state.goals == []
    assert "supervisor_decision" not in state.known_facts


def test_converged_atomic_quote_reuses_existing_quote_items():
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["AGENT_ARCHITECTURE"] = "converged"
    state = CustomerServiceState(
        session_id=f"short-quote-{uuid4().hex}",
        known_facts={"selected_products": [{"product_id": "SKU001", "name": "原味贝果", "quantity": 1, "unit_price": 10}]},
    )
    state, reply, trace = run_turn(state, "多少钱")
    assert reply
    assert trace["next_action"]["tool_name"] == "calculate_order_quote"
    assert state.goals == []
    assert "supervisor_decision" not in state.known_facts
