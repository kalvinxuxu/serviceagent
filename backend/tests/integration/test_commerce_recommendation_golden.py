from backend.app.agent.commerce_agent import CommerceAgent


def test_recommendation_golden_cases_are_in_stock_and_bounded():
    agent = CommerceAgent()
    for text in ("早餐低糖", "给孩子吃的面包", "低糖早餐预算20"):
        result = agent.recommend(text)
        assert len(result) <= 3
        assert all(item.get("available") for item in result)


def test_recommendation_no_exact_match_returns_tradeoff_candidates_or_empty():
    result = CommerceAgent().recommend("低糖早餐")
    assert isinstance(result, list)
