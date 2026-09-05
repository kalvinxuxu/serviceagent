from fastapi import HTTPException
from ..agent.state import CustomerServiceState


def validate_pqg_access(state: CustomerServiceState, owner_id: str | None) -> None:
    if state.owner_customer_id and owner_id != state.owner_customer_id:
        raise HTTPException(status_code=403, detail="SESSION_OWNER_MISMATCH")
