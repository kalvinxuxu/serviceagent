from uuid import uuid4
from .models import OrderDraft, OrderEmail
from .repositories import REPOSITORY, now
from .email_parser import parse_email
from .trace import record

def create_draft(payload) -> tuple[OrderDraft | None, bool]:
    existing = REPOSITORY.emails.get(payload.email_id)
    if existing:
        return REPOSITORY.drafts.get(existing["draft_id"]), True
    parsed = parse_email(payload.subject, payload.body, payload.sender)
    email = OrderEmail(payload.email_id, payload.sender, payload.subject, payload.body, now(), payload.attachment_refs, parsed["classification"], "PARSED")
    if parsed["classification"] != "ORDER":
        email.processing_status = "FAILED"
        REPOSITORY.emails[payload.email_id] = {"email": email, "draft_id": None}
        return None, False
    draft = OrderDraft(f"od_{uuid4().hex[:10]}", payload.email_id, 1, parsed["customer"], parsed["items"], parsed["delivery"], missing_information=parsed["missing_information"], conflicts=parsed["conflicts"])
    if draft.missing_information: draft.status = "NEEDS_CLARIFICATION"
    REPOSITORY.emails[payload.email_id] = {"email": email, "draft_id": draft.draft_id}
    REPOSITORY.drafts[draft.draft_id] = draft
    record(draft.draft_id, "EMAIL_PARSED", "email_parser", context={"item_count": len(draft.items), "missing_count": len(draft.missing_information)})
    return draft, False

def get_draft(draft_id: str) -> OrderDraft | None:
    return REPOSITORY.drafts.get(draft_id)

def patch_draft(draft: OrderDraft, payload) -> OrderDraft:
    if payload.version != draft.version: raise ValueError("VERSION_STALE")
    if payload.items is not None: draft.items = payload.items
    if payload.delivery is not None: draft.delivery = payload.delivery
    if payload.notes is not None: draft.notes = payload.notes
    draft.version += 1; draft.checks = []; draft.reply = None; draft.status = "READY_FOR_CHECK"
    record(draft.draft_id, "DRAFT_EDITED", "draft_service", context={"version": draft.version})
    return draft
