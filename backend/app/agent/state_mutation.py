from __future__ import annotations

from typing import Any

from .reference_resolver import reference_product
from .state import CustomerServiceState


def apply_action(
    state: CustomerServiceState,
    operation: str,
    reference: dict[str, Any],
    quantity: int | None = None,
) -> dict[str, Any]:
    """Apply a validated conversation operation to the working selection."""
    product_ids = list(reference.get("resolved_product_ids", []))
    if reference.get("reference_type") == "AMBIGUOUS":
        return {"status": "AMBIGUOUS", "product_ids": reference.get("candidate_product_ids", [])}
    if operation not in {"KEEP", "REQUOTE"} and not product_ids:
        return {"status": "UNRESOLVED", "product_ids": []}
    selected = [dict(item) for item in state.known_facts.get("selected_products", [])]

    def find(product_id: str) -> dict[str, Any] | None:
        return next((item for item in selected if item.get("product_id") == product_id), None)

    if operation in {"SELECT", "ADD"}:
        for product_id in product_ids:
            product = reference_product(state, {"resolved_product_ids": [product_id]})
            if not product:
                continue
            item = find(product_id)
            amount = quantity or 1
            if item and operation == "ADD":
                item["quantity"] = int(item.get("quantity", 0)) + amount
            elif item:
                item["quantity"] = amount
            else:
                selected.append({"product_id": product_id, "name": product.get("name"), "quantity": amount, "unit_price": product.get("price", 0)})
    elif operation == "REMOVE":
        selected = [item for item in selected if item.get("product_id") not in product_ids]
    elif operation == "SET_QUANTITY":
        for product_id in product_ids:
            item = find(product_id)
            if item:
                item["quantity"] = quantity or 1
    elif operation == "REPLACE":
        selected = [item for item in selected if item.get("product_id") not in product_ids]

    state.known_facts["selected_products"] = selected
    return {"status": "PASS", "product_ids": product_ids, "items": selected, "operation": operation}
