from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState

def test_explicit_handoff_preserves_safe_status():
    state=CustomerServiceState(session_id="s")
    run_turn(state, "请转人工")
    assert state.requires_human and state.status == "HANDOFF"
