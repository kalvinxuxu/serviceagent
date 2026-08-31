from backend.app.domain.catalog import PRODUCTS
from backend.app.domain.inventory_service import InventoryService
from backend.app.repositories.inventory import InMemoryInventoryRepository


def test_inventory_service_derives_status_and_available_quantity():
    service = InventoryService(InMemoryInventoryRepository({
        "SKU001": {"on_hand": 10, "reserved": 3, "updated_at": "2026-01-01T00:00:00+00:00"},
    }))
    result = service.get_current("SKU001")
    assert result["data"]["available_quantity"] == 7
    assert result["data"]["inventory_status"] == "IN_STOCK"


def test_inventory_service_does_not_treat_missing_state_as_zero():
    service = InventoryService(InMemoryInventoryRepository())
    result = service.get_current(PRODUCTS[0]["id"])
    assert result["data"]["inventory_status"] == "UNKNOWN"
    assert result["data"]["available_quantity"] is None

def test_inventory_service_treats_bread_as_parent_category():
    service = InventoryService(InMemoryInventoryRepository({
        "SKU001": {"on_hand": 3, "reserved": 0, "updated_at": "2026-01-01T00:00:00+00:00"},
    }))
    result = service.list_available(category="面包")
    assert result["ok"] is True
    assert any(item["product_id"] == "SKU001" for item in result["data"])


def test_inventory_service_matches_category_in_product_name():
    service = InventoryService(InMemoryInventoryRepository({
        "SKU001": {"on_hand": 3, "reserved": 0, "updated_at": "2026-01-01T00:00:00+00:00"},
        "SKU026": {"on_hand": 3, "reserved": 0, "updated_at": "2026-01-01T00:00:00+00:00"},
    }))
    result = service.list_available(category="吐司")
    assert {item["product_id"] for item in result["data"]} == {"SKU001", "SKU026"}
