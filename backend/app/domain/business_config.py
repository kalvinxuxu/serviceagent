"""Persisted, auditable business boundaries for the virtual shop demo."""

from copy import deepcopy
from uuid import uuid4

from ..db.models.service import BusinessConfig, BusinessConfigAudit
from ..db.session import SessionLocal, init_db
from .policy_service import POLICIES
from .catalog import PRODUCTS
from .inventory_service import get_service

RECOMMENDATION_CONSTRAINTS = {"max_results": 3, "blocked_tags": []}
HANDOFF_CONDITIONS = {
    "max_clarification_turns": 3,
    "reason_codes": ["CLARIFICATION_LOOP", "HUMAN_REQUEST_OR_HIGH_RISK", "TOOL_UNAVAILABLE"],
}
SALES_POLICY = {
    "currency": "CNY",
    "member_discount_rate": 0.95,
    "threshold_discounts": [
        {"threshold": 30, "discount": 3, "label": "满30减3"},
        {"threshold": 50, "discount": 5, "label": "满50减5"},
    ],
    "free_shipping_threshold": 80,
    "shipping_fee": 6,
    "default_delivery_mode": "PICKUP",
    "shipping_provider": "顺丰",
    "shipping_scope": "省内",
    "shipping_subsidy_threshold": 50,
    "shipping_subsidy_rate": 0.5,
    "stacking": "member_discount_then_threshold_discount",
}
FEATURED_LIST = {
    "key": "MUST_EAT",
    "title": "山也面包必吃榜",
    "description": "店内高人气推荐",
    "product_ids": ["SKU001", "SKU007", "SKU009"],
    "enabled": True,
}


def _values() -> dict[str, dict]:
    return {
        "catalog": {"products": deepcopy(PRODUCTS)},
        "return_policy": deepcopy(POLICIES["return"]),
        "recommendation_constraints": deepcopy(RECOMMENDATION_CONSTRAINTS),
        "handoff_conditions": deepcopy(HANDOFF_CONDITIONS),
        "sales_policy": deepcopy(SALES_POLICY),
        "featured_list": deepcopy(FEATURED_LIST),
    }


def load_persisted() -> None:
    init_db()
    with SessionLocal() as db:
        rows = {row.key: row.value for row in db.query(BusinessConfig).all()}
    if rows.get("product_catalog", {}).get("products"):
        # Preserve admin-maintained values while backfilling newly added seed metadata.
        from ..db.seed import load_seed_data
        seed_data = load_seed_data()
        seeded = {item["id"]: {**item, **seed_data.get("product_metadata", {}).get(item["id"], {})}
                  for item in seed_data.get("products", [])}
        persisted_products = []
        for item in rows["product_catalog"]["products"]:
            base = seeded.get(item.get("id"), {})
            persisted_products.append({**base, **{k: v for k, v in item.items() if k != "stock"}})
        PRODUCTS[:] = persisted_products
    if rows.get("return_policy"):
        POLICIES["return"] = rows["return_policy"]
    RECOMMENDATION_CONSTRAINTS.update(rows.get("recommendation_constraints", {}))
    HANDOFF_CONDITIONS.update(rows.get("handoff_conditions", {}))
    SALES_POLICY.update(rows.get("sales_policy", {}))
    FEATURED_LIST.update(rows.get("featured_list", {}))


def update(key: str, value: dict, actor: str = "demo-admin") -> dict:
    init_db()
    with SessionLocal() as db:
        row = db.get(BusinessConfig, key)
        before = deepcopy(row.value) if row else {}
        version = (row.version + 1) if row else 1
        if row:
            row.value = value
            row.version = version
        else:
            db.add(BusinessConfig(key=key, value=value, version=version))
        db.add(BusinessConfigAudit(
            id=uuid4().hex[:32], config_key=key, operation="UPDATE",
            before_value=before, after_value=value, actor=actor,
        ))
        db.commit()
    return {"key": key, "value": value, "version": version}


def audit(key: str | None = None) -> list[dict]:
    init_db()
    with SessionLocal() as db:
        query = db.query(BusinessConfigAudit)
        if key:
            query = query.filter(BusinessConfigAudit.config_key == key)
        return [
            {"id": row.id, "key": row.config_key, "operation": row.operation,
             "before": row.before_value, "after": row.after_value,
             "actor": row.actor, "created_at": row.created_at.isoformat()}
            for row in query.order_by(BusinessConfigAudit.created_at).all()
        ]


def snapshot() -> dict:
    inventory = {product["id"]: get_service().get_current(product["id"]).get("data", {}) for product in PRODUCTS}
    return {
        "products": PRODUCTS,
        "inventory": inventory,
        "return_policy": POLICIES["return"],
        "recommendation_constraints": RECOMMENDATION_CONSTRAINTS,
        "handoff_conditions": HANDOFF_CONDITIONS,
        "sales_policy": SALES_POLICY,
        "featured_list": FEATURED_LIST,
    }
