from datetime import datetime, timezone
from typing import Any
from ..domain.catalog import PRODUCTS
from ..domain.inventory_service import check as check_inventory

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

class OrderRepository:
    def __init__(self):
        self.emails: dict[str, Any] = {}
        self.drafts: dict[str, Any] = {}
        self.replies: dict[str, Any] = {}
        self.sent: dict[str, dict[str, Any]] = {}

    def find_product(self, query: str) -> list[dict[str, Any]]:
        q = query.strip().lower()
        return [p for p in PRODUCTS if q and (q == p.get("id", "").lower() or q in p["name"].lower() or q in p.get("category", "").lower())]

    def inventory(self, product_id: str) -> dict[str, Any]:
        return check_inventory(product_id)

REPOSITORY = OrderRepository()
