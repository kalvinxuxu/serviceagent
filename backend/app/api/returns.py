from fastapi import APIRouter
from ..domain.return_service import check_return_eligibility

router = APIRouter(prefix="/api/v1")

@router.get("/orders/{order_id}/return-eligibility")
def eligibility(order_id: str, customer_id: str = "CUS001"):
    return check_return_eligibility(order_id, customer_id)
