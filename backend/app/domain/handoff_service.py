import json
from uuid import uuid4

from ..db.models.trace import HumanHandoff
from ..db.session import SessionLocal, init_db


def summarize(session) -> dict:
    original_request = session.original_request or next(
        (m.content for m in session.messages if m.role == "user"), ""
    )
    known_facts = dict(session.known_facts)
    if session.customer_id:
        known_facts.setdefault("customer_id", session.customer_id)
    return {
        "session_id": session.session_id,
        "customer_id": session.customer_id,
        "goals": session.goals,
        "known_facts": known_facts,
        "original_request": original_request,
        "completed_steps": session.completed_steps,
        "pending_items": session.pending_items or session.missing_fields,
        "messages": [m.model_dump() for m in session.messages[-6:]],
    }


def create_handoff(session, reason: str, source_agent: str | None = None, target_agent: str = "HUMAN") -> dict:
    """Persist a complete, redacted handoff snapshot for the current session."""
    init_db()
    summary = summarize(session)
    summary["handoff"] = {
        "source_agent": source_agent or getattr(session, "active_agent", "SUPERVISOR"),
        "target_agent": target_agent,
        "task_stack": getattr(session, "task_stack", []),
        "complaint_context": getattr(session, "complaint_context", None),
    }
    handoff_id = uuid4().hex[:32]
    with SessionLocal() as db:
        db.add(
            HumanHandoff(
                id=handoff_id,
                session_id=session.session_id,
                reason=reason,
                context_summary=json.dumps(redact(summary), ensure_ascii=False),
                original_request=summary["original_request"],
                known_facts=summary["known_facts"],
                completed_steps=summary["completed_steps"],
                pending_items=summary["pending_items"],
            )
        )
        db.commit()
    return {"id": handoff_id, "reason": reason, "context": redact(summary)}

def redact(summary: dict) -> dict:
    result = dict(summary)
    if result.get("customer_id"): result["customer_id"] = "***" + result["customer_id"][-2:]
    facts = dict(result.get("known_facts") or {})
    for key in ("phone", "email", "address", "id_number", "token"):
        facts.pop(key, None)
    result["known_facts"] = facts
    return result
