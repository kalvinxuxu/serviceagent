import pytest

from backend.app.agent.contracts import DomainRouteDecision, ExecutionDecision
from backend.app.agent.plan_validator import validate_execution_decision


def test_domain_route_decision_has_no_action_or_handoff_fields():
    decision = DomainRouteDecision(domain="COMMERCE", confidence=0.9, reason_code="DOMAIN_ROUTE")
    assert set(decision.model_dump()) == {"domain", "confidence", "reason_code"}


def test_plan_validator_does_not_rewrite_or_execute_decision():
    decision = ExecutionDecision(kind="TOOL_CALL", action="CHECK_INVENTORY", tool_name="check_inventory", reason_code="R")
    assert validate_execution_decision(decision, {"check_inventory"}) is decision


def test_plan_validator_rejects_capability_mismatch():
    decision = ExecutionDecision(kind="TOOL_CALL", action="CHECK_INVENTORY", tool_name="check_inventory", reason_code="R")
    with pytest.raises(ValueError, match="CAPABILITY_NOT_ALLOWED"):
        validate_execution_decision(decision, set())
