from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from ..pqg.contracts import PQGRequest
from ..pqg.service import generate_suggestions
from ..pqg.repositories import get_result, save_event
from .sessions import _authorize_actor, _session_state

router = APIRouter(prefix="/api/v1")


class PQGEvent(BaseModel):
    request_id: str
    candidate_id: str
    event_type: str


@router.post("/sessions/{session_id}/proactive-questions")
def create_suggestions(session_id: str, request: PQGRequest, x_session_owner: str | None = Header(default=None)):
    state = _session_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    try:
        _authorize_actor(state, state.customer_id, x_session_owner)
    except HTTPException:
        raise
    latest_assistant = next((message for message in reversed(state.messages) if message.role == "assistant"), None)
    if request.session_id != session_id or not request.reply.strip() or latest_assistant is None or str(latest_assistant.content) != request.reply:
        raise HTTPException(status_code=422, detail="ASSISTANT_MESSAGE_NOT_CURRENT")
    server_context = "\n".join(f"{message.role}: {message.content}" for message in state.messages[-8:])
    server_request = request.model_copy(update={"context": server_context, "reply": str(latest_assistant.content)})
    return generate_suggestions(server_request).model_dump(mode="json")


@router.get("/sessions/{session_id}/proactive-questions/{assistant_message_id}")
def get_suggestions(session_id: str, assistant_message_id: str):
    result = get_result(session_id, assistant_message_id)
    if result is None:
        raise HTTPException(status_code=404, detail="PQG_NOT_FOUND")
    return result.model_dump(mode="json")


@router.post("/sessions/{session_id}/proactive-questions/events")
def record_event(session_id: str, event: PQGEvent, x_session_owner: str | None = Header(default=None)):
    state = _session_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    _authorize_actor(state, state.customer_id, x_session_owner)
    if event.event_type not in {"IMPRESSION", "CLICK", "EDIT", "SEND", "IGNORE"}:
        raise HTTPException(status_code=422, detail="INVALID_EVENT_TYPE")
    save_event(session_id, event.request_id, event.candidate_id, event.event_type)
    return {"session_id": session_id, "accepted": True, "event_type": event.event_type}
