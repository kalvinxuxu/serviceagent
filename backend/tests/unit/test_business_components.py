from backend.app.domain.product_service import search
from backend.app.domain.recommendation_service import recommend
from backend.app.domain.policy_service import search as search_policy
from backend.app.agent.handoff_rules import should_handoff

def test_catalog_and_recommendation_components():
    assert search("吐司")
    results = recommend(["低糖"], "早餐")
    assert len(results) <= 3 and all(p["available_quantity"] > 0 for p in results)

def test_policy_and_handoff_components():
    assert search_policy("退货")["days"] == 7
    assert should_handoff("HUMAN_REQUEST_OR_HIGH_RISK")
