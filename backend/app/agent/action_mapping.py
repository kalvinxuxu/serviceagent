from __future__ import annotations

from .contracts import ExecutionDecision, SemanticAction


ATOMIC_TOOL_BY_ACTION = {
    "BROWSE": "list_available_inventory",
    "QUERY": "check_inventory",
    "COMPARE": "compare_products",
    "REQUOTE": "calculate_order_quote",
}


def atomic_decision(action: SemanticAction, *, arguments: dict | None = None) -> ExecutionDecision:
    tool_name = ATOMIC_TOOL_BY_ACTION.get(action.act)
    if not tool_name:
        return ExecutionDecision(kind="STATE_MUTATION", action=action.act, reason_code="STATE_MUTATION_REQUIRED")
    return ExecutionDecision(
        kind="TOOL_CALL",
        action=action.act,
        tool_name=tool_name,
        arguments=arguments or {},
        reason_code=f"{action.act}_REQUIRED",
    )
