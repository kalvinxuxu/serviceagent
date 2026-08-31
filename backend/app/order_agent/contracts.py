from typing import Any, Literal
from pydantic import BaseModel, Field

class OrderEmailInput(BaseModel):
    email_id: str = Field(min_length=1, max_length=120)
    sender: str = Field(min_length=3, max_length=200)
    subject: str = Field(default="", max_length=200)
    body: str = Field(min_length=1, max_length=12000)
    attachment_refs: list[str] = Field(default_factory=list)

class DraftPatch(BaseModel):
    delivery: dict[str, Any] | None = None
    items: list[dict[str, Any]] | None = None
    notes: str | None = None
    version: int = Field(ge=1)

class ConfirmationInput(BaseModel):
    draft_version: int = Field(ge=1)
    confirmed_by: str = Field(min_length=1, max_length=120)
    idempotency_key: str = Field(min_length=1, max_length=200)

class OrderAction(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    action: Literal["PARSE_EMAIL", "CHECK_ORDER", "ASK_USER", "GENERATE_DRAFT", "ASK_CONFIRMATION", "SEND_REPLY", "HANDOFF"]
    arguments: dict[str, Any] = Field(default_factory=dict)

def result(*, ok: bool, data: Any = None, reason: str | None = None, observed_at: str, **extra: Any) -> dict[str, Any]:
    return {"ok": ok, "data": data, "reason": reason, "observed_at": observed_at, "schema_version": "1.0", **extra}
