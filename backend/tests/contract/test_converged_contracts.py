import pytest
from pydantic import ValidationError

from backend.app.agent.contracts import ExecutionDecision, PolicyDecision, ResolvedReference, SemanticAction


def test_execution_contract_rejects_toolless_tool_call():
    with pytest.raises(ValidationError):
        ExecutionDecision(kind="TOOL_CALL", action="QUERY", reason_code="QUERY")


def test_resolved_reference_has_no_business_result_fields():
    result = ResolvedReference(status="RESOLVED", product_ids=["SKU1"], source="CURRENT_CANDIDATES", confidence=1)
    assert result.product_ids == ["SKU1"]


def test_policy_decision_is_separate_from_supervisor_route():
    decision = PolicyDecision(decision="REQUIRE_CONFIRMATION", reason_code="SIDE_EFFECT")
    assert decision.requires_confirmation is False


def test_semantic_action_does_not_require_sku_or_tool():
    action = SemanticAction(act="SET_QUANTITY", quantity=3)
    assert action.target is None
    assert not hasattr(action, "tool_name")
