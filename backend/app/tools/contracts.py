from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

class ToolRequest(BaseModel):
    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)

class ToolObservation(BaseModel):
    ok: bool
    data: Any = None
    reason: str | None = None
    observed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
