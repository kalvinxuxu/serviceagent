from backend.app.agent.goal_stack import transition_goals
from backend.app.agent.state import CustomerServiceState


def test_converged_atomic_request_does_not_create_goal(monkeypatch):
    monkeypatch.setenv("AGENT_ARCHITECTURE", "converged")
    state = CustomerServiceState(session_id="atomic-goal")
    assert transition_goals(state, ["INVENTORY_CHECK"]) == []
    assert state.goals == []


def test_converged_long_transaction_creates_goal(monkeypatch):
    monkeypatch.setenv("AGENT_ARCHITECTURE", "converged")
    state = CustomerServiceState(session_id="long-goal")
    transitions = transition_goals(state, ["RETURN"])
    assert transitions and state.goals[0]["type"] == "RETURN"
