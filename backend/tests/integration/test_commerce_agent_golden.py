from backend.app.agent.commerce_agent import CommerceAgent
from backend.app.agent.state import CustomerServiceState
from backend.app.agent.graph import run_turn


def test_commerce_golden_path_preserves_quote_and_inventory_context(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    state = CustomerServiceState(session_id="commerce-golden")
    state, _, _ = run_turn(state, "两个原味吐司，一个全麦吐司")
    assert state.active_agent == "COMMERCE"
    assert state.quote_context is not None
    assert len(state.quote_context.items) == 2

    state, _, _ = run_turn(state, "那还有什么吐司吗？")
    assert state.active_agent == "COMMERCE"
    assert any(goal["type"] == "INVENTORY_CHECK" for goal in state.goals)


def test_commerce_adapter_is_replaceable_at_task_boundary():
    assert CommerceAgent().capabilities()
