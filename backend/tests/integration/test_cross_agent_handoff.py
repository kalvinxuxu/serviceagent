from backend.app.agent.state import CustomerServiceState
from backend.app.agent.task_manager import create_task, resume_task, update_task
from backend.app.domain.handoff_service import create_handoff


def test_cross_agent_task_can_complete_and_resume_with_context():
    state = CustomerServiceState(session_id="cross-agent", active_agent="COMMERCE")
    state.known_facts["quote_context"] = {"total": 26}
    task = create_task(state, "AFTER_SALES", "HANDLE_COMPLAINT", {"quote_total": 26})
    assert update_task(state, task.id, "COMPLETED")
    resumed = create_task(state, "COMMERCE", "RESUME_QUOTE", {"quote_total": 26})
    assert resume_task(state, resumed.id).status == "RUNNING"
    assert state.task_stack[-1]["relevant_context"]["quote_total"] == 26


def test_handoff_contains_source_target_and_redacted_context():
    state = CustomerServiceState(session_id="handoff-v2", customer_id="CUS001", active_agent="AFTER_SALES")
    state.known_facts["phone"] = "13800000000"
    result = create_handoff(state, "POLICY_CONFLICT", source_agent="AFTER_SALES")
    assert result["context"]["handoff"]["target_agent"] == "HUMAN"
    assert result["context"]["customer_id"].startswith("***")
