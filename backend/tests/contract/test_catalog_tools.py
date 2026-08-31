from backend.app.tools.inventory_tools import check_inventory
from backend.app.tools.product_tools import search_products

def test_catalog_tools_return_component_results():
    assert search_products("吐司")
    assert check_inventory("SKU001")["ok"]
