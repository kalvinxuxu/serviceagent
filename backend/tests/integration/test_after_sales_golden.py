from backend.app.agent.after_sales_agent import AfterSalesAgent
from backend.app.domain.claims_policy_service import evaluate_claim
from backend.app.tools.after_sales_tools import execute_resolution


def test_after_sales_golden_path_requires_policy_and_confirmation():
    context = AfterSalesAgent().classify("商品破损了", "ORD001").model_copy(update={"evidence_status": "RECEIVED"})
    decision = evaluate_claim(context)
    assert decision.policy_version == "claims-v1"
    assert execute_resolution(decision.model_dump(), confirmed=False)["ok"] is False
    result = execute_resolution(decision.model_dump(), confirmed=True, idempotency_key="ORD001:damage")
    assert result["ok"] is True
