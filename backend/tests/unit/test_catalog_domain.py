from backend.app.domain.inventory_service import check
from backend.app.domain.order_service import recent

def test_catalog_domain_handles_known_and_unknown_data():
    assert check("SKU001")["data"]["available_quantity"] >= 0
    assert recent("CUS001")
