from backend.app.order_agent.repositories import OrderRepository
def test_repository_contract_exposes_product_and_inventory_adapters():
    repo=OrderRepository(); assert repo.find_product('原味贝果'); assert repo.inventory('SKU022')['ok']
