from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState

def test_unknown_intent_is_safe():
    state=CustomerServiceState(session_id="s")
    _, reply, trace=run_turn(state, "你好，我想咨询一下")
    assert reply and trace["next_action"]["type"] == "ASK_USER"
