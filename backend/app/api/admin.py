from typing import Any
import json
import os

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile
from pathlib import Path
import tempfile
from pydantic import BaseModel, Field

from ..domain import business_config
from ..domain.catalog import PRODUCTS
from ..domain.policy_service import POLICIES
from ..domain.inventory_service import audit as inventory_audit, get_service
from ..domain.media_service import add_alias, list_media, register_media
from ..domain.product_admin_service import list_product_admin_views
from ..domain.memory_service import read as read_memory, remove as remove_memory
from ..db.seed import sync_product_rows

def require_admin(x_admin_token: str | None = Header(default=None)):
    """Protect admin endpoints when an ADMIN_TOKEN is configured."""
    expected = os.getenv("ADMIN_TOKEN", "").strip()
    if expected and x_admin_token != expected:
        raise HTTPException(status_code=401, detail="ADMIN_AUTH_REQUIRED")
    return True


router = APIRouter(prefix="/api/v1/admin", dependencies=[Depends(require_admin)])
REPORT_ROOT = Path("reports/benchmark")


class ProductUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    price: float | None = Field(default=None, ge=0)
    dine_in_price: float | None = Field(default=None, ge=0)
    member_price: float | None = Field(default=None, ge=0)
    promotion_price: float | None = Field(default=None, ge=0)
    status: str | None = None
    factual_attributes: dict[str, Any] | None = None
    merchandising_attributes: dict[str, Any] | None = None
    audience_fit: list[dict[str, Any]] | None = None
    audience_tags: list[str] | None = None
    scene_tags: list[str] | None = None
    feature_tags: list[str] | None = None
    texture_tags: list[str] | None = None
    flavor_tags: list[str] | None = None
    nutrition_tags: list[str] | None = None
    selling_tags: list[str] | None = None
    selling_points: list[str] | None = None
    allergens: list[str] | None = None


class InventoryUpdate(BaseModel):
    on_hand: int | None = Field(default=None, ge=0)
    reserved: int = Field(default=0, ge=0)
    stock: int | None = Field(default=None, ge=0)
    reason: str = "admin adjustment"


class ReturnPolicyUpdate(BaseModel):
    days: int = Field(ge=0)
    text: str = Field(min_length=1)


class SalesPolicyUpdate(BaseModel):
    currency: str = "CNY"
    member_discount_rate: float = Field(default=0.95, gt=0, le=1)
    threshold_discounts: list[dict[str, Any]] = Field(default_factory=list)
    free_shipping_threshold: float = Field(default=80, ge=0)
    shipping_fee: float = Field(default=6, ge=0)
    stacking: str = "member_discount_then_threshold_discount"


@router.get("/config")
def get_config():
    return business_config.snapshot()


@router.get("/audit")
def get_audit(key: str | None = None):
    return {"items": business_config.audit(key)}


@router.get("/products")
def list_products():
    return {"items": [{**product, "media": list_media(product["id"])} for product in PRODUCTS]}


@router.get("/product-list")
def product_list(category: str | None = None, status: str | None = None,
                 sort_by: str = Query(default="name", pattern="^(name|price_asc|inventory_desc)$")):
    return {"items": [item.model_dump() for item in list_product_admin_views(category, status, sort_by)]}


@router.put("/products/{product_id}")
def update_product(product_id: str, request: ProductUpdate):
    product = next((item for item in PRODUCTS if item["id"] == product_id), None)
    if not product:
        raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")
    payload = request.model_dump(exclude_none=True)
    if "dine_in_price" in payload:
        payload["price"] = payload.pop("dine_in_price")
    product.update(payload)
    business_config.update("product_catalog", {"products": PRODUCTS})
    sync_product_rows()
    return product


@router.post("/products/{product_id}/aliases")
def create_product_alias(product_id: str, request: dict[str, Any]):
    if not any(item["id"] == product_id for item in PRODUCTS):
        raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")
    return add_alias(request.get("alias", ""), product_id, request.get("alias_type", "DISPLAY_NAME"), request.get("source", "MANUAL"))


@router.get("/products/{product_id}/aliases")
def list_product_aliases(product_id: str):
    if not any(item["id"] == product_id for item in PRODUCTS):
        raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")
    return {"items": next(item.aliases for item in list_product_admin_views() if item.id == product_id)}


@router.post("/media")
def create_media(request: dict[str, Any]):
    try:
        return register_media(product_id=request.get("product_id"), asset_type=request.get("asset_type", "PRODUCT_IMAGE"),
                              source_path=request["source_path"], display_name=request.get("display_name", "image"),
                              alt_text=request.get("alt_text", ""))
    except (KeyError, FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))


@router.post("/media/upload")
async def upload_media(product_id: str | None = Form(default=None), asset_type: str = Form(default="PRODUCT_IMAGE"),
                       alt_text: str = Form(default=""), file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
        raise HTTPException(status_code=422, detail="UNSUPPORTED_IMAGE_TYPE")
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(await file.read())
        return register_media(product_id=product_id, asset_type=asset_type,
                              source_path=str(temporary_path), display_name=file.filename or "image",
                              alt_text=alt_text)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    finally:
        if temporary_path:
            temporary_path.unlink(missing_ok=True)


@router.get("/media")
def list_admin_media(product_id: str | None = None):
    return {"items": list_media(product_id)}


@router.get("/customers/{customer_id}/memory")
def get_customer_memory(customer_id: str):
    return {"items": read_memory(customer_id)}


@router.delete("/customers/{customer_id}/memory/{key}")
def delete_customer_memory(customer_id: str, key: str):
    return {"deleted": remove_memory(customer_id, key)}


@router.put("/inventory/{product_id}")
def update_inventory(product_id: str, request: InventoryUpdate):
    on_hand = request.on_hand if request.on_hand is not None else request.stock
    if on_hand is None:
        raise HTTPException(status_code=422, detail="ON_HAND_REQUIRED")
    result = get_service().adjust(product_id, on_hand, request.reserved, request.reason)
    if not result["ok"]:
        code = 404 if result["reason"] == "PRODUCT_NOT_FOUND" else 422
        raise HTTPException(status_code=code, detail=result["reason"])
    return result

@router.get("/inventory-audit")
def get_inventory_audit(product_id: str | None = None):
    return {"items": inventory_audit(product_id)}


@router.put("/return-policy")
def update_return_policy(request: ReturnPolicyUpdate):
    POLICIES["return"] = request.model_dump()
    business_config.update("return_policy", POLICIES["return"])
    return POLICIES["return"]


@router.put("/recommendation-constraints")
def update_recommendation_constraints(request: dict[str, Any]):
    business_config.RECOMMENDATION_CONSTRAINTS.update(request)
    business_config.update("recommendation_constraints", business_config.RECOMMENDATION_CONSTRAINTS)
    return business_config.RECOMMENDATION_CONSTRAINTS


@router.put("/handoff-conditions")
def update_handoff_conditions(request: dict[str, Any]):
    business_config.HANDOFF_CONDITIONS.update(request)
    business_config.update("handoff_conditions", business_config.HANDOFF_CONDITIONS)
    return business_config.HANDOFF_CONDITIONS


@router.put("/sales-policy")
def update_sales_policy(request: SalesPolicyUpdate):
    policy = request.model_dump()
    for rule in policy["threshold_discounts"]:
        if float(rule.get("threshold", 0)) < 0 or float(rule.get("discount", 0)) < 0:
            raise HTTPException(status_code=422, detail="INVALID_THRESHOLD_DISCOUNT")
    business_config.SALES_POLICY.clear()
    business_config.SALES_POLICY.update(policy)
    business_config.update("sales_policy", business_config.SALES_POLICY)
    return business_config.SALES_POLICY


@router.get("/sales-policy")
def get_sales_policy():
    return business_config.SALES_POLICY


@router.get("/featured-list")
def get_featured_list():
    return business_config.FEATURED_LIST


@router.put("/featured-list")
def update_featured_list(request: dict[str, Any]):
    product_ids = request.get("product_ids", [])
    known_ids = {item["id"] for item in PRODUCTS}
    if not isinstance(product_ids, list) or any(item not in known_ids for item in product_ids):
        raise HTTPException(status_code=422, detail="FEATURED_PRODUCT_NOT_FOUND")
    business_config.FEATURED_LIST.update({"title": request.get("title", business_config.FEATURED_LIST["title"]),
                                          "description": request.get("description", business_config.FEATURED_LIST["description"]),
                                          "product_ids": product_ids, "enabled": bool(request.get("enabled", True))})
    business_config.update("featured_list", business_config.FEATURED_LIST)
    return business_config.FEATURED_LIST


@router.post("/featured-list/items/{product_id}")
def add_featured_product(product_id: str):
    if not any(item["id"] == product_id for item in PRODUCTS):
        raise HTTPException(status_code=404, detail="PRODUCT_NOT_FOUND")
    ids = business_config.FEATURED_LIST.setdefault("product_ids", [])
    if product_id not in ids:
        ids.append(product_id)
        business_config.update("featured_list", business_config.FEATURED_LIST)
    return business_config.FEATURED_LIST


@router.delete("/featured-list/items/{product_id}")
def remove_featured_product(product_id: str):
    ids = business_config.FEATURED_LIST.setdefault("product_ids", [])
    business_config.FEATURED_LIST["product_ids"] = [item for item in ids if item != product_id]
    business_config.update("featured_list", business_config.FEATURED_LIST)
    return business_config.FEATURED_LIST


@router.get("/benchmark/latest")
def latest_benchmark():
    reports = sorted(REPORT_ROOT.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not reports:
        raise HTTPException(status_code=404, detail="BENCHMARK_REPORT_NOT_FOUND")
    try:
        return json.loads(reports[0].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        raise HTTPException(status_code=422, detail="BENCHMARK_REPORT_INVALID")
