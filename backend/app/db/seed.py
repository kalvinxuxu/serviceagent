from pathlib import Path
import json
import os

from ..domain.catalog import PRODUCTS
from .models.catalog import InventoryState, Product
from .session import SessionLocal, init_db
from ..domain.media_service import add_alias, register_media

def load_seed_data() -> dict:
    root = Path(__file__).resolve().parents[3] / "data" / "seed"
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in root.glob("*.json")}

def load_products_from_seed() -> None:
    products = load_seed_data().get("products")
    if products:
        metadata = load_seed_data().get("product_metadata", {})
        for product in products:
            product.update(metadata.get(product["id"], {}))
        PRODUCTS[:] = products
    dine_in = load_seed_data().get("dine_in_products", [])
    existing = {item["name"]: item for item in PRODUCTS}
    aliases = {"红豆烧": "日式红豆烧", "芝士肠仔包": "芝士肠仔"}
    for item in dine_in:
        target = existing.get(item["name"])
        if target is None and item["name"] in aliases:
            target = existing.get(aliases[item["name"]])
        if target is not None:
            target["price"] = item["price"]
            target["category"] = item["category"]
            continue
        product = {"id": f"DINE_{len(PRODUCTS) + 1:03d}", "name": item["name"], "category": item["category"],
                   "tags": [], "price": item["price"], "price_channel": "DINE_IN", "inventory_pending": True}
        PRODUCTS.append(product)
        existing[item["name"]] = product


def seed_media_and_aliases() -> None:
    source = Path(os.getenv("BREAD_PICS_DIR", "bread_pics"))
    if not source.exists():
        return
    by_name = {item["name"]: item for item in PRODUCTS}
    mappings = {
        "红豆烧.jpg": ("日式红豆烧", "PRODUCT_IMAGE"),
        "芝士肠仔包.jpg": ("芝士肠仔", "PRODUCT_IMAGE"),
        "必吃榜（6090） v2.1.jpg": (None, "FEATURED_BOARD"),
    }
    for filename, (name, asset_type) in mappings.items():
        path = source / filename
        if not path.exists():
            continue
        product = by_name.get(name) if name else None
        media = register_media(product_id=product["id"] if product else None, asset_type=asset_type,
                               source_path=str(path), display_name=filename, alt_text=name or "山也面包必吃榜")
        if product:
            add_alias(name.replace("日式", ""), product["id"], source="SEED")

def seed_inventory() -> None:
    records = load_seed_data().get("inventory", [])
    init_db()
    with SessionLocal() as db:
        for item in records:
            if db.get(InventoryState, item["product_id"]) is None:
                db.add(InventoryState(
                    product_id=item["product_id"], on_hand=item["on_hand"],
                    reserved=item.get("reserved", 0), version=1,
                ))
        db.commit()


def sync_product_rows() -> None:
    init_db()
    with SessionLocal() as db:
        for item in PRODUCTS:
            profile = {key: item[key] for key in ("factual_attributes", "merchandising_attributes", "audience_fit", "audience_tags", "scene_tags", "feature_tags", "texture_tags", "flavor_tags", "nutrition_tags", "selling_tags", "selling_points", "allergens") if key in item}
            row = db.get(Product, item["id"])
            if row is None:
                row = Product(id=item["id"], name=item["name"], category=item.get("category", ""), price=item.get("price", 0), member_price=item.get("member_price"), promotion_price=item.get("promotion_price"), status=item.get("status", "ON_SALE"), tags=item.get("tags", []), profile=profile, price_channel=item.get("price_channel", "DINE_IN"))
                db.add(row)
            else:
                row.name = item["name"]
                row.category = item.get("category", "")
                row.price = item.get("price", 0)
                row.member_price = item.get("member_price")
                row.promotion_price = item.get("promotion_price")
                row.status = item.get("status", "ON_SALE")
                row.tags = item.get("tags", [])
                row.profile = profile
                row.price_channel = item.get("price_channel", "DINE_IN")
        db.commit()

if __name__ == "__main__":
    data = load_seed_data()
    print(f"Loaded seed datasets: {', '.join(sorted(data))}")
