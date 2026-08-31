from backend.app.db.seed import load_products_from_seed
from backend.app.domain.inventory_service import InventoryService
from backend.app.repositories.inventory import InMemoryInventoryRepository
from backend.app.domain import reservation_service


def _service(monkeypatch, available=1):
    load_products_from_seed()
    inventory = InventoryService(InMemoryInventoryRepository({"SKU044": {"on_hand": available, "reserved": 0, "updated_at": "2026-01-01T00:00:00+00:00"}}))
    monkeypatch.setattr(reservation_service, "get_service", lambda: inventory)
    reservation_service.clear_reservations()
    return inventory


def test_reservation_is_atomic_and_idempotent(monkeypatch):
    inventory = _service(monkeypatch, available=1)
    first = reservation_service.reserve_product(product_id="SKU044", quantity=1, customer_id="CUS001", pickup_time="下午三点", reservation_key="same")
    second = reservation_service.reserve_product(product_id="SKU044", quantity=1, customer_id="CUS001", pickup_time="下午三点", reservation_key="same")
    assert first["ok"] and second["data"]["idempotent"]
    assert inventory.get_current("SKU044")["data"]["available_quantity"] == 0


def test_reservation_rejects_insufficient_stock_without_mutation(monkeypatch):
    inventory = _service(monkeypatch, available=1)
    result = reservation_service.reserve_product(product_id="SKU044", quantity=2, customer_id="CUS002", pickup_time="下午四点", reservation_key="nope")
    assert result["reason"] == "INSUFFICIENT_STOCK"
    assert inventory.get_current("SKU044")["data"]["reserved"] == 0
    assert reservation_service.list_reservations() == []
