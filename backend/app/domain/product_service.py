from .catalog import PRODUCTS

def search(query: str = "", tags: list[str] | None = None) -> list[dict]:
    q = query.strip().lower()
    return [p for p in PRODUCTS if (not q or q in p["name"].lower() or q in p["category"]) and all(t in p["tags"] for t in (tags or []))]

def get(product_id: str) -> dict | None:
    return next((p for p in PRODUCTS if p["id"] == product_id), None)
