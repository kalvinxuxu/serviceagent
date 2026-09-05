from __future__ import annotations

from datetime import datetime, timezone

from .contracts import ExecutionDecision, ToolResult
from ..tools.registry import execute

SIDE_EFFECT_TOOLS = {"create_return_request", "create_delivery_request", "reserve_product", "edit_selected_items", "create_order", "submit_delivery_request"}


class ActionExecutor:
    """Thin execution boundary; business rules remain in Tool/Domain layers."""

    def execute(self, decision: ExecutionDecision) -> ToolResult:
        if decision.kind != "TOOL_CALL" or not decision.tool_name:
            return ToolResult(ok=True, data=None, reason=decision.reason_code)
        if decision.tool_name in SIDE_EFFECT_TOOLS and not decision.arguments.get("confirmed", False):
            return ToolResult(ok=False, data=None, reason="CONFIRMATION_REQUIRED", observed_at=datetime.now(timezone.utc).isoformat())
        return execute(decision.tool_name, decision.arguments)
