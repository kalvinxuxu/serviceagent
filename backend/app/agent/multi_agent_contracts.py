from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from .contracts import DomainRouteDecision


AgentName = Literal["SUPERVISOR", "COMMERCE", "AFTER_SALES", "HUMAN"]
TaskStatus = Literal["CREATED", "RUNNING", "COMPLETED", "BLOCKED", "CANCELLED"]
RouteAction = Literal["CONTINUE_AGENT", "SWITCH_AGENT", "PARALLEL_TASKS", "ASK_USER", "HANDOFF"]
ResolutionLevel = Literal[
    "EXPLAIN",
    "REPLACEMENT",
    "ITEM_REFUND",
    "PARTIAL_REFUND_COMPENSATION",
    "FULL_REFUND",
    "HUMAN_APPROVAL",
]


class AgentTask(BaseModel):
    schema_version: str = "v2"
    id: str
    session_id: str
    task_type: str
    source_agent: AgentName
    target_agent: AgentName
    status: TaskStatus = "CREATED"
    user_message: str = ""
    relevant_context: dict[str, Any] = Field(default_factory=dict)
    required_capabilities: list[str] = Field(default_factory=list)
    parent_task_id: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None

    @model_validator(mode="after")
    def validate_target(self) -> "AgentTask":
        if self.source_agent == self.target_agent and self.task_type.startswith("ROUTE_"):
            raise ValueError("routing task must change agent")
        if self.status == "BLOCKED" and not self.blocked_reason:
            raise ValueError("blocked task requires blocked_reason")
        return self


class SupervisorTask(BaseModel):
    id: str
    target_agent: Literal["COMMERCE", "AFTER_SALES", "HUMAN"]
    status: Literal["READY", "BLOCKED", "COMPLETED"] = "READY"
    depends_on: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None


class SupervisorDecision(BaseModel):
    """Legacy supervisor envelope retained only for compatibility replay.

    Converged mode uses :class:`DomainRouteDecision`, which has no task or
    action fields.  Keeping this adapter prevents breaking v2 consumers while
    stopping new runtime code from depending on its duplicated decisions.
    """
    schema_version: str = "v2"
    goals: list[str] = Field(min_length=1)
    domain: Literal["COMMERCE", "AFTER_SALES", "HUMAN", "UNKNOWN"]
    route_action: RouteAction
    tasks: list[SupervisorTask] = Field(default_factory=list)
    reason_code: str
    confidence: float = Field(ge=0, le=1)
    missing_information: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_tasks(self) -> "SupervisorDecision":
        if self.route_action in {"CONTINUE_AGENT", "SWITCH_AGENT", "PARALLEL_TASKS"} and not self.tasks:
            raise ValueError("agent route requires tasks")
        if self.route_action == "ASK_USER" and not self.missing_information:
            raise ValueError("ASK_USER requires missing_information")
        return self


# Stable name for integrations migrating away from the legacy envelope.
ConvergedSupervisorDecision = DomainRouteDecision


class ComplaintContext(BaseModel):
    issue_type: Literal[
        "WRONG_ITEM", "MISSING_ITEM", "DAMAGED_PRODUCT", "QUALITY_RISK", "DELIVERY_EXCEPTION", "OTHER"
    ]
    order_id: str | None = None
    expected_items: list[dict[str, Any]] = Field(default_factory=list)
    reported_items: list[dict[str, Any]] = Field(default_factory=list)
    customer_claim: str = ""
    evidence_status: Literal["NOT_REQUIRED", "REQUESTED", "RECEIVED", "INSUFFICIENT", "CONFLICTING"] = "REQUESTED"
    severity: Literal["LOW", "MEDIUM", "HIGH", "UNKNOWN"] = "UNKNOWN"
    safety_risk: bool = False
    confidence: float = Field(default=0, ge=0, le=1)


class EvidenceObservation(BaseModel):
    source: str = "IMAGE"
    classification: str = "UNCLASSIFIED"
    confidence: float = Field(default=0, ge=0, le=1)
    evidence_id: str | None = None
    attachment_ids: list[str] = Field(default_factory=list)
    address_candidate: str | None = None
    order_id_candidate: str | None = None
    tracking_number_candidate: str | None = None
    carrier: str | None = None
    observed_facts: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    observed_at: str = "runtime"
    side_effect_allowed: bool = False

    @field_validator("source", mode="before")
    @classmethod
    def normalize_source(cls, value):
        return value if value in {"TEXT", "IMAGE", "ORDER_DATA", "DELIVERY_DATA"} else "IMAGE"

    @field_validator("address_candidate", "order_id_candidate", "tracking_number_candidate", "carrier", mode="before")
    @classmethod
    def normalize_candidate(cls, value):
        if isinstance(value, list):
            value = next((item for item in value if item), None)
        return None if value is None else str(value)

    @field_validator("observed_facts", "uncertainties", mode="before")
    @classmethod
    def normalize_fact_list(cls, value):
        if value is None:
            return []
        if isinstance(value, dict):
            return [f"{key}：{item}" for key, item in value.items()]
        if isinstance(value, str):
            return [value]
        return value if isinstance(value, list) else [str(value)]

    @model_validator(mode="after")
    def validate_observation_content(self) -> "EvidenceObservation":
        if (
            self.classification == "UNCLASSIFIED"
            and not self.address_candidate
            and not self.order_id_candidate
            and not self.tracking_number_candidate
            and not self.observed_facts
        ):
            raise ValueError("visual observation contains no evidence facts")
        return self
    evidence_id: str | None = None
    attachment_ids: list[str] = Field(default_factory=list)
    address_candidate: str | None = None
    order_id_candidate: str | None = None
    tracking_number_candidate: str | None = None
    carrier: str | None = None


class ResolutionDecision(BaseModel):
    issue_type: str
    policy_version: str
    allowed_levels: list[ResolutionLevel] = Field(default_factory=list)
    recommended_level: ResolutionLevel
    options: list[dict[str, Any]] = Field(default_factory=list)
    requires_confirmation: bool = True
    requires_human: bool = False
    reason_code: str

    @model_validator(mode="after")
    def validate_recommendation(self) -> "ResolutionDecision":
        if self.recommended_level not in self.allowed_levels and self.recommended_level != "HUMAN_APPROVAL":
            raise ValueError("recommended resolution must be allowed")
        if self.recommended_level in {"REPLACEMENT", "ITEM_REFUND", "PARTIAL_REFUND_COMPENSATION", "FULL_REFUND"} and not self.requires_confirmation:
            raise ValueError("replacement, refund, or compensation requires confirmation")
        return self
