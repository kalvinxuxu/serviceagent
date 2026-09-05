from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

ActionType = Literal["TOOL_CALL", "ASK_USER", "ASK_CONFIRMATION", "RESPOND", "HANDOFF", "SWITCH_GOAL"]
ConversationOperationType = Literal["ADD", "REMOVE", "SET_QUANTITY", "REPLACE", "KEEP"]
ConversationAct = Literal["REQUEST", "SELECT", "ACCEPT", "REJECT", "ADD", "REMOVE", "MODIFY", "FOLLOW_UP", "CLARIFY"]
GoalStatus = Literal["PENDING", "ACTIVE", "PAUSED", "COMPLETED", "BLOCKED", "ABANDONED"]
SemanticActionType = Literal["BROWSE", "QUERY", "SELECT", "ADD", "REMOVE", "SET_QUANTITY", "KEEP", "COMPARE", "REQUOTE", "SWITCH_TOPIC"]
ReferenceTargetType = Literal["EXPLICIT_PRODUCT", "ORDINAL", "CHEAPEST", "FOCUSED_PRODUCT", "CATEGORY", "PRONOUN"]
ExecutionKind = Literal["STATE_MUTATION", "TOOL_CALL", "ASK_USER", "HANDOFF", "NOOP"]
PolicyDecisionType = Literal["ALLOW", "DENY", "REQUIRE_CONFIRMATION", "ESCALATE"]
ActiveDomain = Literal["COMMERCE", "AFTER_SALES", "UNKNOWN"]
ExecutionMode = Literal["AUTO", "WAITING_USER", "WAITING_CONFIRMATION", "HUMAN_HANDOFF"]


class ReferenceTarget(BaseModel):
    type: ReferenceTargetType
    value: str | int | None = None


class SemanticAction(BaseModel):
    """Provider-neutral semantic act; it never contains SKU or business results."""
    act: SemanticActionType
    target: ReferenceTarget | None = None
    quantity: int | None = Field(default=None, ge=1)
    goal: str | None = None


class ResolvedReference(BaseModel):
    status: Literal["RESOLVED", "AMBIGUOUS", "UNRESOLVED"]
    product_ids: list[str] = Field(default_factory=list)
    source: str | None = None
    confidence: float = Field(default=0, ge=0, le=1)
    ambiguous_candidates: list[str] = Field(default_factory=list)


class ExecutionDecision(BaseModel):
    kind: ExecutionKind
    action: str
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    reason_code: str

    @model_validator(mode="after")
    def validate_execution(self):
        if self.kind == "TOOL_CALL" and not self.tool_name:
            raise ValueError("TOOL_CALL requires tool_name")
        if self.kind != "TOOL_CALL" and self.tool_name:
            raise ValueError("non-tool decision cannot contain tool_name")
        return self


class PolicyDecision(BaseModel):
    decision: PolicyDecisionType
    reason_code: str
    requires_confirmation: bool = False


class DomainRouteDecision(BaseModel):
    """Converged Supervisor contract: domain routing only."""
    domain: ActiveDomain
    confidence: float = Field(ge=0, le=1)
    reason_code: str


class HandoffState(BaseModel):
    reason_code: str
    context: dict[str, Any] = Field(default_factory=dict)
    pending_items: list[str] = Field(default_factory=list)
    status: Literal["PENDING", "ACTIVE", "RESUMABLE", "COMPLETED"] = "PENDING"


class ResponseContext(BaseModel):
    user_text: str
    action: str
    business_result: Any = None
    allowed_facts: dict[str, Any] = Field(default_factory=dict)


class PlannerDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    current_goal_id: str
    goal_type: str = "OTHER"
    action_type: ActionType
    tool_name: str | None = None
    tool_args: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None
    missing_fields: list[str] = Field(default_factory=list)
    reason_code: str
    expected_state_transition: str | None = None

    @model_validator(mode="after")
    def validate_decision(self):
        if self.action_type == "TOOL_CALL" and not self.tool_name:
            raise ValueError("TOOL_CALL requires tool_name")
        if self.action_type != "TOOL_CALL" and self.tool_name:
            raise ValueError("non-tool action cannot contain tool_name")
        return self

class ProductMention(BaseModel):
    text: str
    product_query: str


class RequestedItem(BaseModel):
    query: str
    quantity: int = Field(default=1, ge=1)
    operation: ConversationOperationType = "ADD"
    attributes: list[str] = Field(default_factory=list)
    category: str | None = None


class ConversationOperation(BaseModel):
    operation: ConversationOperationType
    target: str
    quantity: int | None = Field(default=None, ge=1)
    replacement: str | None = None


class MissingSlot(BaseModel):
    name: str
    prompt: str
    priority: int = Field(default=1, ge=1)
    sensitive: bool = False


class ClarificationRequest(BaseModel):
    capability: str
    missing_slots: list[MissingSlot] = Field(default_factory=list)
    next_slot: str | None = None


class ResolvedItem(BaseModel):
    product_id: str
    name: str
    quantity: int = Field(default=1, ge=1)
    operation: ConversationOperationType = "ADD"
    confidence: float = Field(default=1, ge=0, le=1)
    match_type: str = "EXACT_NAME"


class QuoteContext(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    subtotal: float = 0
    discount: float = 0
    shipping: float = 0
    total: float = 0
    currency: str = "CNY"
    status: Literal["DRAFT", "FINAL", "INVALID"] = "DRAFT"
    discount_breakdown: dict[str, Any] = Field(default_factory=dict)
    customer_type: str = "REGULAR"
    next_promotion: dict[str, Any] | None = None
    calculated_at: str | None = None
    delivery_mode: Literal["PICKUP", "SHIPPING"] = "PICKUP"

class UnderstandingOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    goals: list[str] = Field(default_factory=list)
    candidate_goals: list[str] = Field(default_factory=list)
    requested_items: list[RequestedItem] = Field(default_factory=list)
    conversation_operations: list[ConversationOperation] = Field(default_factory=list)
    product_mentions: list[ProductMention] = Field(default_factory=list)
    order_references: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    references: list[str] = Field(default_factory=list)
    requires_clarification: bool = False
    semantic_state: dict[str, Any] = Field(default_factory=dict)
    constraint_updates: dict[str, Any] = Field(default_factory=dict)
    feedback: dict[str, Any] | None = None
    memory_candidate: dict[str, Any] | None = None
    conversation_act: ConversationAct = "REQUEST"
    slot_values: dict[str, Any] = Field(default_factory=dict)
    delivery_intent: bool = False
    delivery_mode: Literal["PICKUP", "SHIPPING", "UNKNOWN"] = "UNKNOWN"

    @model_validator(mode="after")
    def normalize_legacy_fields(self):
        if not self.goals and self.candidate_goals:
            self.goals = list(self.candidate_goals)
        if not self.candidate_goals and self.goals:
            self.candidate_goals = list(self.goals)
        if not self.requested_items and self.product_mentions:
            self.requested_items = [RequestedItem(query=item.product_query or item.text) for item in self.product_mentions]
        if not self.conversation_operations:
            self.conversation_operations = [ConversationOperation(operation=item.operation, target=item.query, quantity=item.quantity) for item in self.requested_items]
        return self


class FeedbackEvent(BaseModel):
    feedback_type: Literal["CORRECTION", "NEGATIVE_PREFERENCE", "CONTEXT_FAILURE", "REFRESH_REQUEST"]
    target_component: str
    previous_value: Any = None
    corrected_value: Any = None
    source: Literal["USER_EXPLICIT", "USER_IMPLICIT", "SYSTEM"] = "USER_EXPLICIT"
    confidence: float = Field(default=1.0, ge=0, le=1)
    raw_text: str | None = None


class PendingFollowup(BaseModel):
    type: Literal["RECOMMEND_PRODUCTS", "ASK_DELIVERY", "ASK_QUANTITY", "CONFIRM_ACTION"]
    source_turn_id: str
    prompt: str
    constraints: dict[str, Any] = Field(default_factory=dict)
    context: dict[str, Any] = Field(default_factory=dict)
    created_at: str | None = None
    expires_after_turns: int = 3


class FollowupIntent(BaseModel):
    type: Literal["ACCEPT_FOLLOWUP", "REJECT_FOLLOWUP", "CLARIFY_FOLLOWUP", "NONE"] = "NONE"
    confidence: float = Field(default=0, ge=0, le=1)
    source: Literal["USER_EXPLICIT", "USER_IMPLICIT", "SYSTEM"] = "USER_EXPLICIT"


class TurnEvaluation(BaseModel):
    understanding_confidence: float = 0
    goal_confidence: float = 0
    entity_resolution: str = "NOT_RUN"
    constraint_extraction: str = "NOT_RUN"
    tool_execution: str = "NOT_RUN"
    business_result_status: str = "NOT_RUN"
    response_grounded: bool = False
    requires_followup: bool = False
    failure_component: str | None = None
    component_scores: dict[str, str] = Field(default_factory=dict)

class Goal(BaseModel):
    type: str
    status: GoalStatus = "ACTIVE"

class NextAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: ActionType
    tool_name: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    message: str | None = None

    @model_validator(mode="after")
    def validate_action(self):
        if self.type == "TOOL_CALL" and not self.tool_name:
            raise ValueError("TOOL_CALL requires tool_name")
        if self.type != "TOOL_CALL" and self.tool_name:
            raise ValueError("non-tool action cannot contain tool_name")
        return self

class PlannerOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str = "1.0"
    goal: Goal
    next_action: NextAction
    reason_code: str
    missing_information: list[str] = Field(default_factory=list)
    requires_confirmation: bool = False
    decision_summary: str | None = None
    current_goal_id: str | None = None
    handoff_offer: bool = False

class ToolResult(BaseModel):
    ok: bool
    data: Any = None
    reason: str | None = None
    observed_at: str
