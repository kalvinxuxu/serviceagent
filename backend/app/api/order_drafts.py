from fastapi import APIRouter, HTTPException
from ..order_agent.contracts import DraftPatch
from ..order_agent.draft_service import get_draft, patch_draft
from ..order_agent.inventory_check import check_draft
from ..order_agent.reply_service import compose_reply

router = APIRouter(prefix="/api/v1")

@router.post("/order-drafts/{draft_id}/check")
def check_order(draft_id: str):
    draft = get_draft(draft_id)
    if not draft: raise HTTPException(404, "DRAFT_NOT_FOUND")
    checks = check_draft(draft); reply = compose_reply(draft)
    return {"draft_id": draft_id, "version": draft.version, "status": draft.status, "checks": checks, "reply": reply}

@router.patch("/order-drafts/{draft_id}")
def edit_order(draft_id: str, payload: DraftPatch):
    draft = get_draft(draft_id)
    if not draft: raise HTTPException(404, "DRAFT_NOT_FOUND")
    try: return patch_draft(draft, payload).view()
    except ValueError as exc: raise HTTPException(409, str(exc))
