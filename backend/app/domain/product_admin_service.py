from __future__ import annotations

from typing import Any

from ..contracts.admin import AdminInventoryView, AdminMediaView, ProductAdminView
from .business_config import FEATURED_LIST, SALES_POLICY
from .catalog import PRODUCTS
from .inventory_service import get_service
from .media_service import list_media
from ..db.models.service import ProductAlias
from ..db.session import SessionLocal, init_db


def _tags(product: dict[str, Any]) -> list[str]:
    values: list[str] = []
    values.extend(str(item) for item in product.get("tags", []) if item)
    profile = _profile(product)
    for key in ("audience_tags", "scene_tags", "feature_tags", "selling_tags", "selling_points", "flavor_tags", "texture_tags", "nutrition_tags"):
        value = profile.get(key, [])
        values.extend(str(item) for item in (value if isinstance(value, list) else [value]) if item)
    for item in product.get("audience_fit", []) or []:
        if isinstance(item, dict) and item.get("value"):
            values.append(str(item["value"]))
    return list(dict.fromkeys(values))[:6]


def _profile(product: dict[str, Any]) -> dict[str, Any]:
    profile = dict(product.get("profile") or {})
    for key in ("audience_tags", "scene_tags", "feature_tags", "texture_tags", "flavor_tags", "nutrition_tags", "selling_tags", "selling_points", "allergens"):
        if key in product:
            profile[key] = product[key]
    return profile


def _view(product: dict[str, Any]) -> ProductAdminView:
    dine_in = float(product.get("dine_in_price", product.get("price", 0)))
    member = product.get("member_price")
    if member is None:
        member = round(dine_in * float(SALES_POLICY.get("member_discount_rate", 0.95)), 2)
    promotion = product.get("promotion_price")
    discounts = [float(value) for value in (member, promotion) if value is not None]
    inventory_result = get_service().get_current(product["id"])
    inventory_data = inventory_result.get("data", {})
    media = list_media(product_id=product["id"], asset_type="PRODUCT_IMAGE")
    primary = media[0] if media else None
    profile = _profile(product)
    if product.get("factual_attributes") is not None:
        profile = {**profile, "factual_attributes": product["factual_attributes"]}
    if product.get("merchandising_attributes") is not None:
        profile = {**profile, "merchandising_attributes": product["merchandising_attributes"]}
    init_db()
    with SessionLocal() as db:
        aliases = [row.alias for row in db.query(ProductAlias).filter_by(product_id=product["id"]).all()]
    return ProductAdminView(
        id=product["id"], name=product["name"], category=product.get("category", ""),
        dine_in_price=dine_in, member_price=member, promotion_price=promotion,
        display_discount_price=min(discounts) if discounts else None,
        inventory=AdminInventoryView(on_hand=inventory_data.get("on_hand"), reserved=inventory_data.get("reserved"), available_quantity=inventory_data.get("available_quantity"), status=inventory_data.get("inventory_status", "UNKNOWN")),
        primary_media=AdminMediaView(media_id=primary["media_id"], url=f"/api/v1/media/{primary['media_id']}", alt=primary.get("alt", product["name"])) if primary else None,
        display_tags=_tags(product), status=product.get("status", "ON_SALE"), profile=profile,
        featured=product["id"] in FEATURED_LIST.get("product_ids", []),
        aliases=aliases,
    )


def list_product_admin_views(category: str | None = None, status: str | None = None, sort_by: str = "name") -> list[ProductAdminView]:
    items = [_view(product) for product in PRODUCTS if (not category or product.get("category") == category) and (not status or product.get("status", "ON_SALE") == status)]
    if sort_by == "price_asc":
        return sorted(items, key=lambda item: item.dine_in_price)
    if sort_by == "inventory_desc":
        return sorted(items, key=lambda item: item.inventory.available_quantity or 0, reverse=True)
    return sorted(items, key=lambda item: item.name)
