from .catalog import PRODUCTS
from .inventory_service import get_service


def compare_products(product_ids: list[str] | None = None, category: str | None = None) -> dict:
    ids = set(product_ids or [])
    candidates = [
        product for product in PRODUCTS
        if (not ids or product["id"] in ids)
        and (not category or product.get("category") == category or category in product.get("name", ""))
    ]
    available = []
    for product in candidates:
        inventory = get_service().get_current(product["id"])
        if inventory.get("ok") and (inventory.get("data", {}).get("available_quantity") or 0) > 0:
            available.append(product)
    if not available:
        return {"ok": False, "reason": "NO_COMPARABLE_PRODUCTS"}
    ordered = sorted(available, key=lambda item: item["price"])
    cheapest = ordered[0]
    return {
        "ok": True,
        "data": {
            "products": [{"product_id": item["id"], "name": item["name"], "price": item["price"]} for item in ordered],
            "cheapest": {"product_id": cheapest["id"], "name": cheapest["name"], "price": cheapest["price"]},
            "difference": round(ordered[-1]["price"] - cheapest["price"], 2) if len(ordered) > 1 else 0,
        },
    }
