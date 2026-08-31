from fastapi import APIRouter
from .sessions import SESSIONS
from ..domain.handoff_service import redact, summarize
from ..db.models.trace import HumanHandoff
from ..db.session import SessionLocal, init_db
from ..conversation_service import load_state

router = APIRouter(prefix="/api/v1")

@router.get("/sessions/{session_id}/handoff")
def handoff_context(session_id: str):
    init_db()
    with SessionLocal() as db:
        handoff = db.query(HumanHandoff).filter(HumanHandoff.session_id == session_id).order_by(HumanHandoff.id.desc()).first()
    if handoff:
        known_facts = dict(handoff.known_facts or {})
        if known_facts.get("customer_id"):
            known_facts["customer_id"] = "***" + str(known_facts["customer_id"])[-2:]
        return {
            "id": handoff.id,
            "reason": handoff.reason,
            "context": {
                "session_id": session_id,
                "original_request": handoff.original_request,
                "known_facts": known_facts,
                "completed_steps": handoff.completed_steps,
                "pending_items": handoff.pending_items,
            },
        }
    state = SESSIONS.get(session_id) or load_state(session_id)
    if state is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    return {"reason": "NOT_CREATED", "context": redact(summarize(state))}
