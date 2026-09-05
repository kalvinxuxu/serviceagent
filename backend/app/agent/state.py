from typing import Any, Literal
from pydantic import BaseModel, Field
from .contracts import ActiveDomain, ExecutionMode, HandoffState, QuoteContext, PendingFollowup

SessionStatus = Literal["IN_PROGRESS", "WAITING_USER", "WAITING_SELECTION", "WAITING_CONFIRMATION", "HANDOFF", "RESOLVED", "FAILED"]

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: Any
    actor_id: str | None = None

class CustomerServiceState(BaseModel):
    session_id: str
    customer_id: str | None = None
    owner_customer_id: str | None = None
    group_member_ids: list[str] = Field(default_factory=list)
    active_customer_id: str | None = None
    customer_contexts: dict[str, dict[str, Any]] = Field(default_factory=dict)
    messages: list[Message] = Field(default_factory=list)
    goals: list[dict[str, Any]] = Field(default_factory=list)
    goal_transitions: list[dict[str, Any]] = Field(default_factory=list)
    known_facts: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    current_plan: list[dict[str, Any]] = Field(default_factory=list)
    tool_results: list[dict[str, Any]] = Field(default_factory=list)
    requires_confirmation: bool = False
    requires_human: bool = False
    status: SessionStatus = "IN_PROGRESS"
    turn_count: int = 0
    original_request: str | None = None
    completed_steps: list[str] = Field(default_factory=list)
    pending_items: list[str] = Field(default_factory=list)
    quote_context: QuoteContext | None = None
    state_version: int = 1
    recent_products: list[dict[str, Any]] = Field(default_factory=list)
    focused_product: dict[str, Any] | None = None
    current_order: dict[str, Any] | None = None
    complaint_context: dict[str, Any] | None = None
    active_agent: Literal["SUPERVISOR", "COMMERCE", "AFTER_SALES", "HUMAN"] = "SUPERVISOR"
    active_domain: ActiveDomain = "UNKNOWN"
    execution_mode: ExecutionMode = "AUTO"
    handoff_state: HandoffState | None = None
    task_stack: list[dict[str, Any]] = Field(default_factory=list)
    handoff_history: list[dict[str, Any]] = Field(default_factory=list)
    semantic_state: dict[str, Any] = Field(default_factory=dict)
    feedback_events: list[dict[str, Any]] = Field(default_factory=list)
    turn_evaluations: list[dict[str, Any]] = Field(default_factory=list)
    conversation_act: str = "REQUEST"
    missing_slots: list[dict[str, Any]] = Field(default_factory=list)
    recommendation_candidates: list[str] = Field(default_factory=list)
    reference_context: dict[str, Any] = Field(default_factory=dict)
    delivery_slots: dict[str, Any] = Field(default_factory=dict)
    delivery_mode: Literal["PICKUP", "SHIPPING"] = "PICKUP"
    pending_evidence: dict[str, Any] | None = None
    evidence_history: list[dict[str, Any]] = Field(default_factory=list)
    logistics_context: dict[str, Any] | None = None
    pending_followup: PendingFollowup | None = None
    pending_followup_history: list[dict[str, Any]] = Field(default_factory=list)

    def add_message(self, role: str, content: str, actor_id: str | None = None) -> None:
        self.messages.append(Message(role=role, content=content, actor_id=actor_id))
