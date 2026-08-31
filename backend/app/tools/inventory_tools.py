from ..domain.inventory_service import check

def check_inventory(product_id: str):
    return check(product_id)
