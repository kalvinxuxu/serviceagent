from backend.app.agent.after_sales_agent import AfterSalesAgent
from backend.app.agent.multi_agent_contracts import ComplaintContext
from backend.app.domain.claims_policy_service import evaluate_claim


def test_after_sales_classifies_damage_and_policy_returns_ladder():
    context = AfterSalesAgent().classify("收到的面包破损了")
    decision = evaluate_claim(context.model_copy(update={"evidence_status": "RECEIVED"}))
    assert context.issue_type == "DAMAGED_PRODUCT"
    assert "REPLACEMENT" in decision.allowed_levels


def test_insufficient_evidence_only_explains_or_handoffs():
    decision = evaluate_claim(ComplaintContext(issue_type="WRONG_ITEM", evidence_status="INSUFFICIENT"))
    assert decision.recommended_level == "EXPLAIN"
