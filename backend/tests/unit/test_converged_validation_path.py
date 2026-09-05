import os

from backend.app.agent.action_planner import to_execution_decision
from backend.app.agent.contracts import Goal, NextAction, PlannerOutput
from backend.app.agent.plan_validator import validate_execution_decision


def test_converged_validation_preserves_valid_action():
    os.environ["AGENT_ARCHITECTURE"] = "converged"
    output = PlannerOutput(
        goal=Goal(type="INVENTORY_CHECK"),
        next_action=NextAction(type="TOOL_CALL", tool_name="check_inventory", arguments={"product_id": "SKU001"}),
        reason_code="R",
    )
    decision = to_execution_decision(output)
    assert validate_execution_decision(decision, {"check_inventory"}) is decision
