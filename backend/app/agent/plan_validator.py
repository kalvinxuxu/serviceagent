from .capability_resolver import resolve_capabilities
from .contracts import Goal, NextAction, PlannerOutput

DELIVERY_SIDE_EFFECT_TOOLS = {"create_delivery_request", "submit_delivery_request", "create_order"}


def validate_plan(output: PlannerOutput, capabilities: list[str]) -> PlannerOutput:
    action = output.next_action
    if action.type == "TOOL_CALL" and action.tool_name in DELIVERY_SIDE_EFFECT_TOOLS:
        slots = action.arguments.get("delivery_slots", {})
        required = ("delivery_address", "recipient_name", "phone")
        missing = [name for name in required if not slots.get(name)]
        if missing:
            return PlannerOutput(
                goal=Goal(type="SHIPPING_POLICY"),
                next_action=NextAction(type="ASK_USER", message=f"还需要提供{missing[0]}后才能继续配送登记。"),
                reason_code="DELIVERY_SLOT_REQUIRED",
                missing_information=missing,
                current_goal_id=output.current_goal_id,
            )
        if not action.arguments.get("confirmed"):
            return PlannerOutput(
                goal=Goal(type="SHIPPING_POLICY"),
                next_action=NextAction(type="ASK_CONFIRMATION", message="配送信息已收集完整，是否确认提交配送登记？"),
                reason_code="DELIVERY_CONFIRMATION_REQUIRED",
                requires_confirmation=True,
                current_goal_id=output.current_goal_id,
            )
    if action.type == "TOOL_CALL" and action.tool_name not in capabilities:
        return PlannerOutput(
            goal=Goal(type=output.goal.type, status="BLOCKED"),
            next_action=NextAction(type="HANDOFF", message="当前请求超出可用业务能力，我为你转人工处理。"),
            reason_code="CAPABILITY_NOT_ALLOWED",
            current_goal_id=output.current_goal_id,
        )
    return output


def validate_for_goal(output: PlannerOutput) -> PlannerOutput:
    return validate_plan(output, resolve_capabilities(output.goal.type))
