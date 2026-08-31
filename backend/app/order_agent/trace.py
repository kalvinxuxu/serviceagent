from .repositories import now

TRACE: dict[str, list[dict]] = {}

def record(draft_id: str, event_type: str, component: str, status: str = "SUCCEEDED", reason_code: str | None = None, context: dict | None = None) -> dict:
    event = {"trace_id": f"tr_{len(TRACE.get(draft_id, [])) + 1}", "draft_id": draft_id, "event_type": event_type, "component": component, "schema_version": "1.0", "occurred_at": now(), "status": status, "reason_code": reason_code, "redacted_context": context or {}}
    TRACE.setdefault(draft_id, []).append(event)
    return event

def get_trace(draft_id: str) -> list[dict]:
    return TRACE.get(draft_id, [])
