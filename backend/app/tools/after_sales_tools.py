from typing import Any


def execute_resolution(decision: dict[str, Any], *, confirmed: bool, human_approved: bool = False, idempotency_key: str | None = None) -> dict[str, Any]:
    level = decision.get("recommended_level")
    if level in {"REPLACEMENT", "ITEM_REFUND", "PARTIAL_REFUND_COMPENSATION", "FULL_REFUND"}:
        if not confirmed:
            return {"ok": False, "reason": "CONFIRMATION_REQUIRED"}
        if decision.get("requires_human") and not human_approved:
            return {"ok": False, "reason": "HUMAN_APPROVAL_REQUIRED"}
        if not idempotency_key:
            return {"ok": False, "reason": "IDEMPOTENCY_KEY_REQUIRED"}
    return {"ok": True, "status": "EXECUTED", "idempotency_key": idempotency_key}
