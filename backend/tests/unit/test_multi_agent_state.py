from backend.app.agent.state_policy import can_write, redact_context
from backend.app.agent.state import CustomerServiceState


def test_shared_state_has_v2_fields_and_version():
    state = CustomerServiceState(session_id="s1")
    assert state.state_version == 1
    assert state.active_agent == "SUPERVISOR"
    assert state.task_stack == []


def test_state_write_scopes_and_handoff_redaction():
    assert can_write("COMMERCE", "quote_context")
    assert not can_write("SUPERVISOR", "quote_context")
    assert redact_context({"name": "A", "phone": "secret"}) == {"name": "A"}
