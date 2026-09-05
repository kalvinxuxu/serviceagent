import os
from uuid import uuid4

from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed


load_products_from_seed()


def test_quantity_only_followup_uses_focused_product():
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["AGENT_ARCHITECTURE"] = "converged"
    state = CustomerServiceState(session_id=f"fq-focused-{uuid4().hex}")
    state, _, first = run_turn(state, "有芝士贝果吗")
    state, reply, second = run_turn(state, "那要两个")
    assert first["reason_code"] == "ATOMIC_INVENTORY_QUERY"
    assert second["reason_code"] == "CAPABILITY_RECOVERED_STATE_MUTATION"
    assert state.known_facts["selected_products"][0]["quantity"] == 2
    assert "26" in reply


def test_category_quantity_mutation_updates_selected_item():
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["AGENT_ARCHITECTURE"] = "converged"
    state = CustomerServiceState(
        session_id=f"fq-category-{uuid4().hex}",
        known_facts={"selected_products": [{"product_id": "SKU022", "name": "原味贝果", "quantity": 1, "unit_price": 10}]},
    )
    state, _, trace = run_turn(state, "贝果改成三个")
    assert state.known_facts["selected_products"][0]["quantity"] == 3
    assert trace["reason_code"] in {"CAPABILITY_RECOVERED_STATE_MUTATION", "ATOMIC_QUOTE_QUERY"}
