from backend.app.agent.action_planner import should_use_planner, to_execution_decision
from backend.app.agent.contracts import Goal, NextAction, PlannerOutput


def test_atomic_work_does_not_require_planner():
    assert should_use_planner(has_condition=False, step_count=1, crosses_domain=False) is False


def test_complex_work_uses_optional_planner():
    assert should_use_planner(has_condition=True, step_count=1, crosses_domain=False) is True


def test_planner_output_adapts_to_execution_decision():
    output = PlannerOutput(
        goal=Goal(type="INVENTORY_CHECK"),
        next_action=NextAction(type="TOOL_CALL", tool_name="check_inventory", arguments={"product_id": "SKU001"}),
        reason_code="R",
    )
    decision = to_execution_decision(output)
    assert decision.kind == "TOOL_CALL"
    assert decision.tool_name == "check_inventory"
