from backend.app.domain.inventory_service import check

class FakeInventory:
    def check(self, product_id): return {"ok": True, "data": {"product_id": product_id, "stock": 99, "available": True}}

def test_inventory_component_can_be_replaced_by_contract_shape():
    result = FakeInventory().check("SKU001")
    assert result.keys() >= {"ok", "data"}
    assert set(check("SKU001").keys()) >= {"ok", "data", "observed_at"}
