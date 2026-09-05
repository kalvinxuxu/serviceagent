from uuid import uuid4
from ..db.session import SessionLocal, init_db
from ..db.models.pqg import PQGInteractionEvent, PQGRequestRecord


def get_result(session_id: str, assistant_message_id: str):
    from .service import _RESULTS
    cached = _RESULTS.get((session_id, assistant_message_id))
    if cached:
        return cached
    init_db()
    with SessionLocal() as db:
        row = db.query(PQGRequestRecord).filter_by(session_id=session_id, assistant_message_id=assistant_message_id).first()
        if not row:
            return None
        from .contracts import PQGResponse
        result = PQGResponse.model_validate(row.response_json)
        _RESULTS[(session_id, assistant_message_id)] = result
        return result


def save_result(result):
    from .service import _RESULTS
    _RESULTS[(result.session_id, result.assistant_message_id)] = result
    init_db()
    with SessionLocal() as db:
        row = PQGRequestRecord(id=result.request_id, session_id=result.session_id, assistant_message_id=result.assistant_message_id, status=result.status.value, response_json=result.model_dump(mode="json"), latency_ms=result.latency_ms)
        db.merge(row)
        db.commit()
    return result


def save_event(session_id: str, request_id: str, candidate_id: str, event_type: str) -> None:
    init_db()
    with SessionLocal() as db:
        db.add(PQGInteractionEvent(id=f"pqge_{uuid4().hex[:10]}", session_id=session_id, request_id=request_id, candidate_id=candidate_id, event_type=event_type))
        db.commit()
