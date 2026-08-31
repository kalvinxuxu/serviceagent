from backend.app.agent.commerce_agent import CommerceAgent


def test_recommendation_agent_uses_typed_preferences_and_catalog_candidates():
    result = CommerceAgent().recommend("早餐想要低糖")
    assert len(result) <= 3
    assert all("id" in item and "available_quantity" in item for item in result)
