from .catalog import find_recent_orders, get_order

def recent(customer_id: str) -> list[dict]:
    return find_recent_orders(customer_id)

def detail(order_id: str) -> dict | None:
    return get_order(order_id)

def status(order_id: str) -> str | None:
    order = get_order(order_id)
    return order["status"] if order else None
