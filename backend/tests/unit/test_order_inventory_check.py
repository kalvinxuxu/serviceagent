from backend.app.order_agent.product_resolver import resolve
def test_product_resolver_returns_unique_product():
    assert resolve('原味贝果')['id'] == 'SKU022'
