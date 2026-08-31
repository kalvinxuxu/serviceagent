import json

from evals.benchmark import load_cases
from evals.benchmark_assertions import bootstrap_fixture, expected_quote, score_case
from backend.app.agent.state import CustomerServiceState


def test_benchmark_has_twenty_versioned_cases():
    cases = load_cases("customer_service_v1")
    assert len(cases) == 20
    assert {case["id"] for case in cases} == {f"SC-{index:02d}" for index in range(1, 21)}


def test_fixture_uses_seed_catalog_and_policy_snapshot():
    fixture = bootstrap_fixture()
    assert fixture["product_count"] >= 40
    assert fixture["fixture_version"]
    assert fixture["sales_policy"]["free_shipping_threshold"] == 80


def test_quote_assertion_uses_domain_service_result():
    fixture = bootstrap_fixture()
    quote = expected_quote([{"product_name": "芝士贝果", "quantity": 2}])
    assert quote["data"]["subtotal"] == 26
    result = score_case(
        {"id": "SC-02", "turns": [{"user": "两个芝士贝果多少钱？"}], "expected": {"goals": ["PRICE_CALCULATION"], "entities": [{"product_name": "芝士贝果", "quantity": 2}], "required_capabilities": ["calculate_order_quote"], "result_type": "QUOTE"}},
        [CustomerServiceState(session_id="test")],
        [{"goal": {"type": "PRICE_CALCULATION"}, "next_action": {"tool_name": "calculate_order_quote"}}],
        ["26元"], fixture,
    )
    assert result["scores"]["business_result"] == 0
