from backend.app.trace_service import get, record_agent_task, record_agent_transition


def test_agent_task_and_transition_are_persisted_as_versioned_trace():
    session_id = "ses_v2_trace"
    record_agent_task(session_id, {"task_id": "t1", "target_agent": "COMMERCE"})
    record_agent_transition(session_id, {"from_agent": "SUPERVISOR", "to_agent": "COMMERCE", "reason_code": "COMMERCE"})
    steps = get(session_id)
    assert steps[-2]["step_type"] == "agent_task"
    assert steps[-1]["step_type"] == "agent_transition"
    assert all(step["schema_version"] == "v2" for step in steps[-2:])
