from fastapi import APIRouter, HTTPException
from ..order_agent.contracts import OrderEmailInput
from ..order_agent.draft_service import create_draft, get_draft

router = APIRouter(prefix="/api/v1")

@router.post("/order-emails")
def ingest_email(payload: OrderEmailInput):
    draft, duplicate = create_draft(payload)
    if draft is None: return {"email_id": payload.email_id, "status": "NON_ORDER"}
    return {"email_id": payload.email_id, "draft_id": draft.draft_id, "status": "DUPLICATE" if duplicate else draft.status, "missing_information": draft.missing_information}

@router.get("/order-drafts/{draft_id}")
def retrieve_draft(draft_id: str):
    draft = get_draft(draft_id)
    if not draft: raise HTTPException(404, "DRAFT_NOT_FOUND")
    return draft.view()
