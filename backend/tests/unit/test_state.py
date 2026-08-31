from backend.app.agent.state import CustomerServiceState

def test_state_message_and_status_fields():
    state=CustomerServiceState(session_id="s")
    state.add_message("user", "你好")
    assert state.messages[0].content == "你好"
    assert state.status == "IN_PROGRESS"
