from backend.app.agent.state_policy import can_write


def test_supervisor_can_write_domain_but_not_handoff_context():
    assert can_write("SUPERVISOR", "active_domain")
    assert not can_write("SUPERVISOR", "handoff_state")


def test_human_can_write_execution_mode():
    assert can_write("HUMAN", "execution_mode")
