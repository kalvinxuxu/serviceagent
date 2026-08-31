from backend.app.domain.recommendation_request import canonicalize_recommendation_request
from backend.app.agent.recommendation_planner_rules import recommendation_arguments


def test_quantity_becomes_recommendation_count():
    request = canonicalize_recommendation_request({"budget": 20, "category": "贝果", "quantity": 2})
    assert request.count == 2
    assert request.category == "贝果"
    assert request.max_price == 20


def test_category_list_becomes_categories_and_one_each():
    request = canonicalize_recommendation_request({"budget": 30, "category": ["吐司", "贝果"]})
    assert request.categories == ["吐司", "贝果"]
    assert request.count == 2


def test_sweetness_enum_is_case_insensitive():
    request = canonicalize_recommendation_request({"sweetness": "low"})
    assert request.constraints["sweetness"] == "LOW"


def test_generic_quantity_extraction_handles_recommendation_phrasing():
    args = recommendation_arguments("20块以内推荐两个不同的贝果", constraints={"budget": 20, "category": "贝果", "different": True})
    assert args["count"] == 2


def test_generic_quantity_and_budget_can_appear_before_request_verb():
    args = recommendation_arguments("25块以内给我搭两个不同的面包", constraints={"different": True, "category": "面包"})
    assert args["count"] == 2
    assert args["max_price"] == 25.0
    assert "category" not in args


def test_budget_and_count_are_extracted_from_category_request():
    args = recommendation_arguments("20块以内两个不同的贝果，怎么选", constraints={"category": "贝果"})
    assert args["count"] == 2
    assert args["max_price"] == 20.0
