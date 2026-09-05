from __future__ import annotations

from typing import Any

from .state import CustomerServiceState


def resolve_semantic_target(state: CustomerServiceState, target: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve a Semantic Workspace target without calling an LLM or inventing SKU."""
    target = target or {}
    target_type = target.get("type", "NONE")
    value = target.get("value")
    if target_type == "REFERENCE":
        marker = str(value or "").upper()
        if marker in {"CHEAPEST", "最便宜", "最便宜的"}:
            return resolve_reference(state, text="最便宜的")
        if marker in {"FIRST", "第一", "第一款", "FIRST_PRODUCT"}:
            return resolve_reference(state, text="第一款")
        if marker in {"SECOND", "第二", "第二个", "SECOND_PRODUCT"}:
            return resolve_reference(state, text="第二个")
        if marker in {"FOCUSED", "FOCUSED_PRODUCT", "刚才那个", "那个", "这个"}:
            return resolve_reference(state)
        return resolve_reference(state)
    if target_type == "PRODUCT" and isinstance(value, str):
        from ..domain.catalog import PRODUCTS
        product = next((item for item in PRODUCTS if item.get("name") == value), None)
        if product:
            return {"reference_type": "EXPLICIT_PRODUCT", "resolved_product_ids": [product["id"]], "confidence": 1.0}
    if target_type == "CATEGORY" and isinstance(value, str):
        from ..domain.catalog import PRODUCTS
        categories = {product.get("id"): product.get("category") for product in PRODUCTS}
        selected = [
            item for item in state.known_facts.get("selected_products", [])
            if item.get("category") == value or categories.get(item.get("product_id")) == value
        ]
        if len(selected) == 1:
            return {"reference_type": "CATEGORY_SELECTED", "resolved_product_ids": [selected[0]["product_id"]], "confidence": 0.95}
        if len(selected) > 1:
            return {"reference_type": "AMBIGUOUS", "resolved_product_ids": [], "candidate_product_ids": [item["product_id"] for item in selected], "confidence": 0.0}
    return {"reference_type": "NONE", "resolved_product_ids": [], "confidence": 0.0}


def resolve_reference(state: CustomerServiceState, resolved_items: list[dict[str, Any]] | None = None, text: str = "") -> dict[str, Any]:
    """Resolve an implicit business reference without inventing a SKU."""
    current = [item for item in (resolved_items or []) if item.get("product_id")]
    if current:
        return {"reference_type": "CURRENT_TURN", "resolved_product_ids": [item["product_id"] for item in current], "confidence": 1.0}
    reference_context = state.reference_context or state.known_facts.get("reference_context", {})
    candidate_ids = reference_context.get("candidate_set", [])
    if candidate_ids and isinstance(candidate_ids[0], dict):
        candidate_ids = [item.get("product_id") for item in candidate_ids]
    ranked = state.known_facts.get("recommendations", [])
    if not ranked and not candidate_ids:
        candidate_ids = list(state.recommendation_candidates)
    if not ranked and candidate_ids:
        from ..domain.catalog import PRODUCTS
        by_id = {item.get("id"): item for item in PRODUCTS}
        ranked = [by_id[item_id] for item_id in candidate_ids if item_id in by_id]
    if text and ranked and any(token in text for token in ("最便宜", "最便宜的", "最贵", "最贵的")):
        usable = [item for item in ranked if item.get("price") is not None]
        if usable:
            chosen = min(usable, key=lambda item: float(item.get("price", 0))) if "最便宜" in text else max(usable, key=lambda item: float(item.get("price", 0)))
            product_id = chosen.get("product_id") or chosen.get("id")
            if product_id:
                return {"reference_type": "RELATIVE_PRICE", "resolved_product_ids": [product_id], "confidence": 0.96}
    if text and ranked:
        rank = next((index for index, words in enumerate(("第一", "第二", "第三"), 1) if f"{words}款" in text or f"{words}个" in text), None)
        if rank and rank <= len(ranked):
            return {"reference_type": "RECOMMENDATION_RANK", "resolved_product_ids": [ranked[rank - 1].get("id")], "confidence": 0.96}
    if state.focused_product and state.focused_product.get("product_id"):
        return {"reference_type": "FOCUSED_PRODUCT", "resolved_product_ids": [state.focused_product["product_id"]], "confidence": 0.98}
    recent = [item for item in state.recent_products if item.get("product_id")]
    if len(recent) == 1:
        return {"reference_type": "RECENT_PRODUCT", "resolved_product_ids": [recent[0]["product_id"]], "confidence": 0.94}
    if len(recent) > 1:
        return {"reference_type": "AMBIGUOUS", "resolved_product_ids": [], "candidate_product_ids": [item["product_id"] for item in recent], "confidence": 0.0}
    selected = state.known_facts.get("selected_products", [])
    if len(selected) == 1 and selected[0].get("product_id"):
        return {"reference_type": "SELECTED_PRODUCTS", "resolved_product_ids": [selected[0]["product_id"]], "confidence": 0.96}
    candidates = list(dict.fromkeys(candidate_ids or state.recommendation_candidates))
    if len(candidates) == 1:
        return {"reference_type": "RECOMMENDATION_CANDIDATE", "resolved_product_ids": candidates, "confidence": 0.9}
    if len(candidates) > 1:
        return {"reference_type": "AMBIGUOUS", "resolved_product_ids": [], "candidate_product_ids": candidates, "confidence": 0.0}
    return {"reference_type": "NONE", "resolved_product_ids": [], "confidence": 0.0}


def reference_product(state: CustomerServiceState, reference: dict[str, Any]) -> dict[str, Any] | None:
    product_id = next(iter(reference.get("resolved_product_ids", [])), None)
    if not product_id:
        return None
    if state.focused_product and state.focused_product.get("product_id") == product_id:
        return dict(state.focused_product)
    for item in state.known_facts.get("selected_products", []) + state.recent_products + state.known_facts.get("recommendations", []):
        if item.get("product_id") == product_id or item.get("id") == product_id:
            return dict(item)
    # Browse results may persist only candidate IDs. Resolve the already
    # selected ID against the catalog; never infer or create a product here.
    from ..domain.catalog import PRODUCTS
    product = next((item for item in PRODUCTS if item.get("id") == product_id), None)
    return dict(product) if product else None
    return None
