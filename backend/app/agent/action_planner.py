from __future__ import annotations

from .contracts import ExecutionDecision, NextAction, PlannerOutput


def to_execution_decision(output: PlannerOutput) -> ExecutionDecision:
    """Adapt the legacy-shaped planner result to the converged execution contract."""
    action: NextAction = output.next_action
    kind = {
        "TOOL_CALL": "TOOL_CALL",
        "ASK_USER": "ASK_USER",
        "ASK_CONFIRMATION": "ASK_USER",
        "HANDOFF": "HANDOFF",
        "RESPOND": "NOOP",
    }.get(action.type, "NOOP")
    return ExecutionDecision(
        kind=kind,
        action=action.type,
        tool_name=action.tool_name if kind == "TOOL_CALL" else None,
        arguments=action.arguments if kind == "TOOL_CALL" else {},
        requires_confirmation=output.requires_confirmation or action.type == "ASK_CONFIRMATION",
        reason_code=output.reason_code,
    )


def should_use_planner(*, has_condition: bool, step_count: int, crosses_domain: bool) -> bool:
    """Planner is opt-in for complex execution only."""
    return has_condition or step_count > 1 or crosses_domain
