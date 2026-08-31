from typing import Any, Literal

from pydantic import BaseModel, Field


StateField = Literal[
    "recent_products",
    "current_order",
    "complaint_context",
    "active_agent",
    "task_stack",
    "handoff_history",
    "quote_context",
]


class StateWritePolicy(BaseModel):
    field: StateField
    readers: list[str] = Field(default_factory=list)
    writers: list[str] = Field(default_factory=list)
    redact_for_handoff: bool = True
    version: int = 1


DEFAULT_STATE_POLICIES = [
    StateWritePolicy(field="recent_products", readers=["SUPERVISOR", "COMMERCE"], writers=["COMMERCE"]),
    StateWritePolicy(field="current_order", readers=["SUPERVISOR", "AFTER_SALES"], writers=["AFTER_SALES"]),
    StateWritePolicy(field="complaint_context", readers=["SUPERVISOR", "AFTER_SALES"], writers=["AFTER_SALES"]),
    StateWritePolicy(field="active_agent", readers=["SUPERVISOR", "HUMAN"], writers=["SUPERVISOR"]),
    StateWritePolicy(field="task_stack", readers=["SUPERVISOR", "COMMERCE", "AFTER_SALES"], writers=["SUPERVISOR"]),
    StateWritePolicy(field="handoff_history", readers=["SUPERVISOR", "HUMAN"], writers=["SUPERVISOR"]),
    StateWritePolicy(field="quote_context", readers=["SUPERVISOR", "COMMERCE"], writers=["COMMERCE"]),
]


def can_write(agent: str, field: StateField) -> bool:
    return any(policy.field == field and agent in policy.writers for policy in DEFAULT_STATE_POLICIES)


def redact_context(context: dict[str, Any]) -> dict[str, Any]:
    hidden = {"phone", "email", "address", "id_number", "token"}
    return {key: value for key, value in context.items() if key.lower() not in hidden}
