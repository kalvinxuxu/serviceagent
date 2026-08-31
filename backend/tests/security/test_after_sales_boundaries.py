from backend.app.tools.after_sales_tools import execute_resolution


def test_evidence_or_policy_cannot_execute_without_confirmation():
    decision = {"recommended_level": "ITEM_REFUND", "requires_human": False}
    assert execute_resolution(decision, confirmed=False)["reason"] == "CONFIRMATION_REQUIRED"
    assert execute_resolution(decision, confirmed=True)["reason"] == "IDEMPOTENCY_KEY_REQUIRED"


def test_human_approval_is_required_for_escalated_resolution():
    decision = {"recommended_level": "FULL_REFUND", "requires_human": True}
    result = execute_resolution(decision, confirmed=True, idempotency_key="k1")
    assert result["reason"] == "HUMAN_APPROVAL_REQUIRED"
