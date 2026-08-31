from backend.app.domain.pricing_service import PricingService


def test_order_quote_supports_multiple_items_and_quantities():
    result = PricingService().calculate_order_quote([
        {"product_id": "SKU022", "quantity": 2},
        {"product_id": "SKU026", "quantity": 1},
    ])
    assert result["ok"] is True
    assert result["data"]["subtotal"] == 34
    assert result["data"]["discount"] == 3
    assert result["data"]["shipping"] == 0
    assert result["data"]["delivery_mode"] == "PICKUP"
    assert result["data"]["total"] == 31


def test_sales_policy_applies_threshold_member_and_free_shipping_rules():
    service = PricingService()
    result = service.calculate_order_quote([{"product_id": "SKU022", "quantity": 5}], customer_type="MEMBER")
    assert result["ok"] is True
    assert result["data"]["regular_subtotal"] == 50
    assert result["data"]["items"][0]["unit_price"] == 9.5
    assert result["data"]["discount_breakdown"]["threshold"] == 5
    assert result["data"]["shipping"] == 0
    assert result["data"]["total"] == 42.5


def test_shipping_policy_uses_customer_paid_fee_and_fifty_percent_subsidy(monkeypatch):
    from backend.app.domain.business_config import SALES_POLICY
    monkeypatch.setitem(SALES_POLICY, "shipping_subsidy_threshold", 50)
    monkeypatch.setitem(SALES_POLICY, "shipping_subsidy_rate", 0.5)
    service = PricingService()
    under_threshold = service.calculate_order_quote([{"product_id": "SKU028", "quantity": 1}], delivery_mode="SHIPPING")
    assert under_threshold["data"]["shipping"] == 6
    at_subsidy = service.calculate_order_quote([{"product_id": "SKU022", "quantity": 5}], delivery_mode="SHIPPING")
    assert at_subsidy["data"]["shipping"] == 3
    assert at_subsidy["data"]["shipping_subsidy"] == 3
    at_free_shipping = service.calculate_order_quote([{"product_id": "SKU022", "quantity": 8}], delivery_mode="SHIPPING")
    assert at_free_shipping["data"]["shipping"] == 0


def test_quote_suggests_next_threshold():
    result = PricingService().calculate_order_quote([{"product_id": "SKU022", "quantity": 4}])
    assert result["data"]["next_promotion"]["threshold"] == 50
    assert result["data"]["next_promotion"]["remaining"] == 10
