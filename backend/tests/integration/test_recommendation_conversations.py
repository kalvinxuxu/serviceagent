from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState

def test_recommendation_conversation_returns_candidates():
    state=CustomerServiceState(session_id="s")
    _, reply, trace=run_turn(state, "给孩子早餐吃，有什么低糖的？")
    assert reply and trace["next_action"]["type"] == "TOOL_CALL"
