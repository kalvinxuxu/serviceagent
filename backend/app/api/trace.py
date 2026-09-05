from fastapi import APIRouter
from ..trace_service import get
from ..conversation_service import load_state

router = APIRouter(prefix="/api/v1")

@router.get("/sessions/{session_id}/trace")
def trace(session_id: str):
    state = load_state(session_id)
    return {
        "session_id": session_id,
        "steps": get(session_id, include_lineage=True),
        "active_agent": state.active_agent if state else None,
        "active_domain": state.active_domain if state else None,
        "execution_mode": state.execution_mode if state else None,
        "handoff_state": state.handoff_state.model_dump() if state and state.handoff_state else None,
        "task_stack": state.task_stack if state else [],
        "handoff_history": state.handoff_history if state else [],
        "route_reason": (state.known_facts.get("supervisor_decision", {}) if state else {}).get("reason_code"),
    }
