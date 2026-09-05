import pytest

from backend.app.agent.state import CustomerServiceState


def test_human_handoff_is_execution_mode_not_domain():
    state = CustomerServiceState(session_id="handoff-state")
    state.execution_mode = "HUMAN_HANDOFF"
    state.active_domain = "AFTER_SALES"
    assert state.execution_mode == "HUMAN_HANDOFF"
    assert state.active_domain == "AFTER_SALES"


def test_active_domain_rejects_human():
    with pytest.raises(ValueError):
        CustomerServiceState(session_id="invalid-domain", active_domain="HUMAN")
