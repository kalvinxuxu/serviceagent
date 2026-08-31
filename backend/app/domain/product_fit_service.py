from __future__ import annotations

from .catalog import PRODUCTS


def explain_product_fit(product_id: str, audience: str | None = None, concern: str | None = None) -> dict:
    product = next((item for item in PRODUCTS if item["id"] == product_id), None)
    if not product:
        return {"ok": False, "reason": "PRODUCT_NOT_FOUND"}
    audience = {"CHILD": "儿童", "SENIOR": "老人", "ELDERLY": "老人", "儿童": "儿童", "老人": "老人"}.get(str(audience or "").upper(), audience or "")
    concern = concern or "audience"
    audience_tags = product.get("audience_tags", [])
    texture_tags = product.get("texture_tags", [])
    evidence = []
    if concern == "texture":
        if texture_tags:
            evidence = [{"field": "texture", "values": texture_tags}]
            status = "SUPPORTED" if any(value in {"柔软", "松软"} for value in texture_tags) else "UNKNOWN"
        else:
            status = "UNKNOWN"
    elif audience in audience_tags:
        evidence = [{"field": "audience", "value": audience}]
        status = "SUPPORTED"
    elif audience_tags:
        status = "NOT_SUPPORTED"
    else:
        status = "UNKNOWN"
    return {
        "ok": True,
        "product_id": product_id,
        "product_name": product["name"],
        "audience": audience,
        "concern": concern,
        "fit_status": status,
        "evidence": evidence,
        "selling_points": product.get("selling_points", []),
    }
