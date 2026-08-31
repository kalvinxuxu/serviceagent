from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..base import Base

class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class AgentStep(Base):
    __tablename__ = "agent_steps"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(32))
    step_type: Mapped[str] = mapped_column(String(50))
    output_summary: Mapped[str] = mapped_column(Text, default="")
    component: Mapped[str | None] = mapped_column(String(60), nullable=True)
    turn_id: Mapped[str | None] = mapped_column(String(40), nullable=True)
    input_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    output_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    before_state: Mapped[dict] = mapped_column(JSON, default=dict)
    after_state: Mapped[dict] = mapped_column(JSON, default=dict)
    latency_ms: Mapped[float | None] = mapped_column(nullable=True)
    step_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class ToolCall(Base):
    __tablename__ = "tool_calls"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(32))
    tool_name: Mapped[str] = mapped_column(String(80))
    arguments: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)

class HumanHandoff(Base):
    __tablename__ = "human_handoffs"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(32))
    reason: Mapped[str] = mapped_column(String(120))
    context_summary: Mapped[str] = mapped_column(Text, default="")
    original_request: Mapped[str] = mapped_column(Text, default="")
    known_facts: Mapped[dict] = mapped_column(JSON, default=dict)
    completed_steps: Mapped[list] = mapped_column(JSON, default=list)
    pending_items: Mapped[list] = mapped_column(JSON, default=list)
