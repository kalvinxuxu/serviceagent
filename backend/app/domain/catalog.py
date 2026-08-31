from datetime import datetime, timezone

PRODUCTS = [
    {"id": "SKU001", "name": "原味吐司", "category": "早餐", "tags": ["低糖", "儿童"], "price": 12},
    {"id": "SKU002", "name": "全麦吐司", "category": "早餐", "tags": ["低糖", "高纤", "儿童"], "price": 16},
    {"id": "SKU003", "name": "低糖贝果", "category": "早餐", "tags": ["低糖", "儿童"], "price": 14},
    {"id": "SKU004", "name": "巧克力贝果", "category": "早餐", "tags": ["甜味"], "price": 15},
    {"id": "SKU005", "name": "可颂", "category": "早餐", "tags": ["酥皮"], "price": 18},
]

ORDERS = {
    "ORD001": {"id": "ORD001", "customer_id": "CUS001", "status": "已送达", "tracking_number": "SF100000001", "item_id": "SKU004", "item_name": "巧克力贝果", "purchased_days_ago": 1},
    "ORD002": {"id": "ORD002", "customer_id": "CUS001", "status": "运输中", "tracking_number": "SF100000002", "item_id": "SKU002", "item_name": "全麦吐司", "purchased_days_ago": 2},
}

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def search_products(query: str = "", tags: list[str] | None = None) -> list[dict]:
    q = query.lower().strip()
    tags = tags or []
    return [p for p in PRODUCTS if (not q or q in p["name"].lower() or q in p["category"]) and all(t in p["tags"] for t in tags)]

def check_inventory(product_id: str) -> dict:
    from .inventory_service import check
    return check(product_id)

def find_recent_orders(customer_id: str) -> list[dict]:
    return [o for o in ORDERS.values() if o["customer_id"] == customer_id]

def get_order(order_id: str) -> dict | None:
    return ORDERS.get(order_id)
