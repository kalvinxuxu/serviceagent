from backend.app.domain.preference_service import normalize
from backend.app.domain.recommendation_service import recommend

def test_recommendation_obeys_hard_constraints():
    constraints=normalize("给孩子早餐吃低糖的")
    results=recommend(constraints["tags"], constraints["category"])
    assert len(results) <= 3 and all(p["available_quantity"] > 0 for p in results)
