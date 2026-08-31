from datetime import datetime, timezone
from uuid import uuid4

from ..repositories.inventory import InventoryRepository, SqliteInventoryRepository
from ..db.models.service import InventoryAudit
from ..db.session import SessionLocal, init_db
from .catalog import PRODUCTS

InventoryStatus = str
LOW_STOCK_THRESHOLD = 5
BREAD_CATEGORIES = {"贝果", "欧包", "吐司", "小面包", "盐面包", "早餐"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _iso(value) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


class InventoryService:
    def __init__(self, repository: InventoryRepository | None = None):
        self.repository = repository or SqliteInventoryRepository()

    def get_current(self, product_id: str) -> dict:
        product = next((item for item in PRODUCTS if item["id"] == product_id), None)
        if product is None:
            return {"ok": False, "reason": "PRODUCT_NOT_FOUND", "observed_at": _now()}
        inventory = self.repository.get_current(product_id)
        if inventory is None:
            return {
                "ok": True,
                "data": {
                    "product_id": product_id, "name": product["name"],
                    "inventory_status": "UNKNOWN", "on_hand": None,
                    "reserved": None, "available_quantity": None, "available": False,
                },
                "observed_at": _now(),
            }
        on_hand = inventory.on_hand if hasattr(inventory, "on_hand") else inventory["on_hand"]
        reserved = inventory.reserved if hasattr(inventory, "reserved") else inventory["reserved"]
        updated_at = inventory.updated_at if hasattr(inventory, "updated_at") else inventory["updated_at"]
        available_quantity = max(on_hand - reserved, 0)
        status = "OUT_OF_STOCK" if available_quantity == 0 else "LOW_STOCK" if available_quantity <= LOW_STOCK_THRESHOLD else "IN_STOCK"
        return {
            "ok": True,
            "data": {
                "product_id": product_id, "name": product["name"],
                "inventory_status": status, "on_hand": on_hand, "reserved": reserved,
                "available_quantity": available_quantity, "available": available_quantity > 0,
            },
            "observed_at": _iso(updated_at),
        }

    def list_available(self, category: str | None = None, query: str = "", max_results: int = 20) -> dict:
        if category in {"面包", "面包类", "烘焙面包"}:
            category_filter = lambda product: product["category"] in BREAD_CATEGORIES or any(term in product["name"] for term in ("面包", "吐司", "贝果", "欧包", "可颂"))
        else:
            category_filter = lambda product: not category or product["category"] == category or category in product["name"]
        candidates = [p for p in PRODUCTS if category_filter(p) and (not query or query in p["name"])]
        items = []
        for product in candidates:
            result = self.get_current(product["id"])
            data = result.get("data", {})
            if (data.get("available_quantity") or 0) > 0:
                items.append({**product, "product_id": product["id"], **{key: data[key] for key in ("inventory_status", "on_hand", "reserved", "available_quantity", "available")}})
        return {"ok": True, "data": items[:max_results], "observed_at": _now()}

    def adjust(self, product_id: str, on_hand: int, reserved: int = 0, reason: str = "", actor: str = "demo-admin") -> dict:
        if not any(item["id"] == product_id for item in PRODUCTS):
            return {"ok": False, "reason": "PRODUCT_NOT_FOUND", "observed_at": _now()}
        if on_hand < 0 or reserved < 0 or reserved > on_hand:
            return {"ok": False, "reason": "INVALID_INVENTORY_QUANTITY", "observed_at": _now()}
        before = self.repository.get_current(product_id)
        self.repository.upsert(product_id, on_hand, reserved)
        if isinstance(self.repository, SqliteInventoryRepository):
            init_db()
            with SessionLocal() as db:
                db.add(InventoryAudit(
                    id=uuid4().hex[:32], product_id=product_id,
                    before_on_hand=getattr(before, "on_hand", None),
                    before_reserved=getattr(before, "reserved", None),
                    after_on_hand=on_hand, after_reserved=reserved,
                    reason=reason, actor=actor,
                ))
                db.commit()
        return self.get_current(product_id)


_SERVICE = InventoryService()


def get_service() -> InventoryService:
    return _SERVICE


def check(product_id: str) -> dict:
    return _SERVICE.get_current(product_id)

def list_available(category: str | None = None, query: str = "", max_results: int = 20) -> dict:
    return _SERVICE.list_available(category, query, max_results)

def check_items(items: list[dict]) -> dict:
    results = []
    for item in items:
        result = _SERVICE.get_current(item["product_id"])
        if not result.get("ok"):
            return result
        results.append({"product_id": item["product_id"], "name": result["data"]["name"], "requested_quantity": item.get("quantity", 1), **result["data"]})
    return {"ok": True, "data": results, "observed_at": _now()}

def audit(product_id: str | None = None) -> list[dict]:
    init_db()
    with SessionLocal() as db:
        query = db.query(InventoryAudit)
        if product_id:
            query = query.filter(InventoryAudit.product_id == product_id)
        return [{
            "id": row.id, "product_id": row.product_id,
            "before": {"on_hand": row.before_on_hand, "reserved": row.before_reserved},
            "after": {"on_hand": row.after_on_hand, "reserved": row.after_reserved},
            "reason": row.reason, "actor": row.actor, "created_at": row.created_at.isoformat(),
        } for row in query.order_by(InventoryAudit.created_at).all()]
