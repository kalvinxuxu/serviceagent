from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState

def test_return_flow_waits_for_confirmation():
    state=CustomerServiceState(session_id="s", customer_id="CUS001")
    run_turn(state, "我昨天买的东西想退")
    run_turn(state, "确认退货")
    assert state.requires_confirmation
