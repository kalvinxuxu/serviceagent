from .repositories import REPOSITORY, now
from .trace import record

def check_draft(draft):
    results = []
    for item in draft.items:
        matches = REPOSITORY.find_product(item.get("product_name") or item.get("raw_description", ""))
        if len(matches) != 1:
            results.append({"item_id": item["item_id"], "fulfillment_status": "UNKNOWN", "match_status": "AMBIGUOUS" if matches else "NOT_FOUND", "reason": "AMBIGUOUS_PRODUCT" if matches else "PRODUCT_NOT_FOUND", "observed_at": now()}); continue
        product = matches[0]; inv = REPOSITORY.inventory(product["id"])
        if not inv.get("ok") or not inv.get("data") or inv["data"].get("available_quantity") is None:
            results.append({"item_id": item["item_id"], "product_id": product["id"], "product_name": product["name"], "fulfillment_status": "UNKNOWN", "reason": "INVENTORY_UNAVAILABLE", "observed_at": inv.get("observed_at", now())}); continue
        requested = float(item["requested_quantity"]); available = inv["data"]["available_quantity"]
        status = "FULFILLABLE" if available >= requested else "PARTIAL" if available > 0 else "OUT_OF_STOCK"
        results.append({"item_id": item["item_id"], "product_id": product["id"], "product_name": product["name"], "requested_quantity": requested, "available_quantity": available, "fulfillment_status": status, "unit_price": product.get("price"), "currency": "CNY", "observed_at": inv.get("observed_at", now())})
    draft.checks = results; draft.status = "CHECKED" if results else "NEEDS_CLARIFICATION"
    if any(x["fulfillment_status"] == "UNKNOWN" for x in results): draft.status = "NEEDS_CLARIFICATION"
    record(draft.draft_id, "INVENTORY_CHECKED", "inventory_check", context={"item_count": len(results)})
    return results
