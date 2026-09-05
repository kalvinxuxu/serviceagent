import pytest

from backend.app.agent.contracts import ExecutionDecision
from backend.app.agent.plan_validator import validate_execution_decision


def test_plan_validator_preserves_valid_decision():
    decision = ExecutionDecision(kind="TOOL_CALL", action="CHECK", tool_name="check_inventory", reason_code="R")
    assert validate_execution_decision(decision, {"check_inventory"}) is decision


def test_plan_validator_rejects_prohibited_tool():
    decision = ExecutionDecision(kind="TOOL_CALL", action="REFUND", tool_name="refund_without_confirmation", reason_code="R")
    with pytest.raises(ValueError, match="CAPABILITY_NOT_ALLOWED"):
        validate_execution_decision(decision, set())
