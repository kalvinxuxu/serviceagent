from backend.app.agent.contracts import Goal, NextAction, PlannerOutput
from backend.app.agent.plan_validator import validate_plan


def _delivery_output(arguments):
    return PlannerOutput(
        goal=Goal(type="SHIPPING_POLICY"),
        next_action=NextAction(type="TOOL_CALL", tool_name="create_delivery_request", arguments=arguments),
        reason_code="DELIVERY_SUBMIT",
    )


def test_delivery_side_effect_requires_all_slots():
    output = validate_plan(_delivery_output({"delivery_slots": {"delivery_address": "上海市"}}), ["create_delivery_request"])
    assert output.reason_code == "DELIVERY_SLOT_REQUIRED"
    assert output.next_action.type == "ASK_USER"


def test_delivery_side_effect_requires_confirmation_after_slots_complete():
    output = validate_plan(_delivery_output({"delivery_slots": {"delivery_address": "上海市", "recipient_name": "张三", "phone": "13800000000"}}), ["create_delivery_request"])
    assert output.reason_code == "DELIVERY_CONFIRMATION_REQUIRED"
    assert output.next_action.type == "ASK_CONFIRMATION"
