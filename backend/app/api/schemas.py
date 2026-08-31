from pydantic import BaseModel, Field

class SessionResponse(BaseModel):
    session_id: str
    status: str

class MessageResponse(BaseModel):
    role: str
    content: str
    actor_id: str | None = None

class InspectorResponse(BaseModel):
    goal: dict | None = None
    next_action: dict | None = None
    reason_code: str | None = None
    status: str | None = None

class ChatResponse(BaseModel):
    session_id: str
    message: MessageResponse
    status: str
    requires_confirmation: bool
    requires_human: bool
    order_summary: dict | None = None
    order_summaries: dict[str, dict] = Field(default_factory=dict)
    actor_id: str | None = None
    inspector: dict = Field(default_factory=dict)
