from .catalog import ORDERS, PRODUCTS, now

RETURN_REQUESTS: dict[str, dict] = {}

def check_return_eligibility(order_id: str, customer_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order or order["customer_id"] != customer_id:
        return {"eligible": False, "reason": "ORDER_NOT_FOUND"}
    if order["purchased_days_ago"] > 7:
        return {"eligible": False, "reason": "RETURN_WINDOW_EXPIRED"}
    return {"eligible": True, "reason": "WITHIN_RETURN_WINDOW"}

def create_return_request(order_id: str, customer_id: str, confirmed: bool) -> dict:
    if not confirmed:
        return {"ok": False, "reason": "CONFIRMATION_REQUIRED"}
    key = f"{customer_id}:{order_id}"
    if key in RETURN_REQUESTS:
        return {"ok": True, "data": RETURN_REQUESTS[key], "reason": "IDEMPOTENT_EXISTING"}
    request = {"id": f"RET{len(RETURN_REQUESTS)+1:03d}", "order_id": order_id, "customer_id": customer_id, "status": "SUBMITTED", "created_at": now()}
    RETURN_REQUESTS[key] = request
    return {"ok": True, "data": request}
