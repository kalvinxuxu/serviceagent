from .repositories import REPOSITORY, now
from .trace import record

def confirm(reply, payload):
    if payload.draft_version != reply["draft_version"]: raise ValueError("VERSION_STALE")
    existing = REPOSITORY.sent.get(payload.idempotency_key)
    if existing: return existing
    reply.update({"status": "CONFIRMED", "confirmed_by": payload.confirmed_by, "confirmed_at": now(), "idempotency_key": payload.idempotency_key})
    record(reply["draft_id"], "REPLY_CONFIRMED", "send_service", context={"version": payload.draft_version})
    return reply

def send(reply):
    if reply.get("status") != "CONFIRMED": raise ValueError("CONFIRMATION_REQUIRED")
    key = reply["idempotency_key"]
    if key in REPOSITORY.sent: return REPOSITORY.sent[key]
    result = {"reply_id": reply["reply_id"], "status": "SENT", "provider_message_id": f"sim_{key}", "sent_at": now(), "idempotency_key": key}
    REPOSITORY.sent[key] = result; reply.update(result)
    record(reply["draft_id"], "REPLY_SENT", "send_service", context={"provider_message_id": result["provider_message_id"]})
    return result
