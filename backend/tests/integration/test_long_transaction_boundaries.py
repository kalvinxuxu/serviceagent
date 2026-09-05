from backend.app.agent.goal_stack import transition_goals
from backend.app.agent.state import CustomerServiceState


def test_return_is_long_transaction_but_atomic_inventory_is_not(monkeypatch):
    monkeypatch.setenv("AGENT_ARCHITECTURE", "converged")
    state = CustomerServiceState(session_id="long-boundary")
    assert transition_goals(state, ["INVENTORY_CHECK"]) == []
    assert transition_goals(state, ["RETURN"])
