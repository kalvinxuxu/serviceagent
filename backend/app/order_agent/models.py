from dataclasses import dataclass, field
from typing import Any

@dataclass
class OrderEmail:
    email_id: str
    sender: str
    subject: str
    body: str
    received_at: str
    attachment_refs: list[str] = field(default_factory=list)
    classification: str = "NEEDS_REVIEW"
    processing_status: str = "RECEIVED"

@dataclass
class OrderDraft:
    draft_id: str
    email_id: str
    version: int
    customer: dict[str, Any]
    items: list[dict[str, Any]]
    delivery: dict[str, Any]
    currency: str = "CNY"
    notes: str = ""
    missing_information: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    checks: list[dict[str, Any]] = field(default_factory=list)
    reply: dict[str, Any] | None = None
    status: str = "READY_FOR_CHECK"

    def view(self) -> dict[str, Any]:
        return {"draft_id": self.draft_id, "email_id": self.email_id, "version": self.version, "customer": self.customer, "items": self.items, "delivery": self.delivery, "currency": self.currency, "notes": self.notes, "missing_information": self.missing_information, "conflicts": self.conflicts, "checks": self.checks, "reply": self.reply, "status": self.status}
