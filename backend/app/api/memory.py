from fastapi import APIRouter, HTTPException

from ..domain.memory_service import read, remove, write

router = APIRouter(prefix="/api/v1/customers")


@router.get("/{customer_id}/memory")
def get_memory(customer_id: str):
    return {"items": read(customer_id)}


@router.put("/{customer_id}/memory")
def put_memory(customer_id: str, candidate: dict):
    result = write(customer_id, {**candidate, "explicit": True, "source": "USER_EXPLICIT"})
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("reason"))
    return result


@router.delete("/{customer_id}/memory/{key}")
def delete_memory(customer_id: str, key: str):
    return {"deleted": remove(customer_id, key)}
