from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.trace_service import get
from uuid import uuid4


def test_trace_is_read_from_database_after_runtime_cache_is_gone():
    state = CustomerServiceState(session_id=f"ses_persist_test_{uuid4().hex[:8]}", customer_id="CUS001")
    run_turn(state, "全麦吐司还有货吗？")

    # The trace API must not depend on an in-process dictionary/cache.
    assert get(state.session_id)
    assert any(item["step_type"] == "planner" for item in get(state.session_id))
    assert get(state.session_id)[-1]["step_type"] == "tool_call"
