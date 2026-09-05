import os
from uuid import uuid4

from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed


load_products_from_seed()


def test_ambiguous_quantity_followup_only_clarifies():
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["AGENT_ARCHITECTURE"] = "converged"
    state = CustomerServiceState(
        session_id=f"ambiguous-{uuid4().hex}",
        recent_products=[
            {"product_id": "SKU022", "name": "原味贝果"},
            {"product_id": "SKU026", "name": "生吐司"},
        ],
    )
    state, reply, trace = run_turn(state, "来两个")
    assert trace["reason_code"] == "AMBIGUOUS_REFERENCE"
    assert trace["next_action"]["type"] == "ASK_USER"
    assert state.known_facts.get("selected_products", []) == []
    assert "两个" not in reply or "哪一款" in reply
