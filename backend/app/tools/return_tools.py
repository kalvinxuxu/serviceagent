from ..domain.return_service import check_return_eligibility, create_return_request

def check_eligibility(order_id: str, customer_id: str): return check_return_eligibility(order_id, customer_id)
def create_request(order_id: str, customer_id: str, confirmed: bool): return create_return_request(order_id, customer_id, confirmed)
