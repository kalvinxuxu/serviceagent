from backend.app.agent.state import CustomerServiceState
from backend.app.agent.graph import run_turn

def test_unknown_intent_asks_user():
    state=CustomerServiceState(session_id="s", customer_id="CUS001")
    state, reply, trace=run_turn(state, "你好，我想咨询一下")
    assert state.status == "WAITING_USER"
    assert trace["next_action"]["type"] == "ASK_USER"

def test_inventory_query_uses_tool():
    state=CustomerServiceState(session_id="s", customer_id="CUS001")
    state, reply, trace=run_turn(state, "全麦吐司还有货吗？")
    assert "全麦吐司" in reply and "有货" in reply
    assert trace["next_action"]["type"] == "TOOL_CALL"

def test_return_requires_confirmation_and_is_idempotent():
    state=CustomerServiceState(session_id="s", customer_id="CUS001")
    run_turn(state, "我昨天买的东西想退")
    run_turn(state, "确认退货")
    assert state.status == "WAITING_CONFIRMATION"
    state, reply, _=run_turn(state, "确认", confirmed=True)
    assert state.status == "RESOLVED"
    assert "RET" in reply
