from ..domain.order_service import recent, detail, status

def find_recent_orders(customer_id: str): return recent(customer_id)
def get_order(order_id: str): return detail(order_id)
def get_order_status(order_id: str): return status(order_id)
