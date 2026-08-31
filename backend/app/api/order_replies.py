from fastapi import APIRouter, HTTPException
from ..order_agent.contracts import ConfirmationInput
from ..order_agent.draft_service import get_draft
from ..order_agent.send_service import confirm, send

router = APIRouter(prefix="/api/v1")

def _reply(reply_id: str):
    for draft in __import__("backend.app.order_agent.repositories", fromlist=["REPOSITORY"]).REPOSITORY.drafts.values():
        if draft.reply and draft.reply.get("reply_id") == reply_id: return draft.reply, draft
    raise HTTPException(404, "REPLY_NOT_FOUND")

@router.post("/reply-drafts/{reply_id}/confirm")
def confirm_reply(reply_id: str, payload: ConfirmationInput):
    reply, _ = _reply(reply_id)
    try: return confirm(reply, payload)
    except ValueError as exc: raise HTTPException(409, str(exc))

@router.post("/reply-drafts/{reply_id}/send")
def send_reply(reply_id: str):
    reply, _ = _reply(reply_id)
    try: return send(reply)
    except ValueError as exc: raise HTTPException(409, str(exc))
