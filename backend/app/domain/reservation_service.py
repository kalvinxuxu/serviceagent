from datetime import datetime, timezone
from threading import Lock
from uuid import uuid4

from .catalog import PRODUCTS
from .inventory_service import get_service
from ..repositories.inventory import InMemoryInventoryRepository
from ..db.models.catalog import InventoryState
from ..db.models.service import InventoryReservation
from ..db.session import SessionLocal, init_db

_LOCK = Lock()
_RESERVATIONS: dict[str, dict] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clear_reservations() -> None:
    with _LOCK:
        _RESERVATIONS.clear()


def list_reservations() -> list[dict]:
    service = get_service()
    if not isinstance(service.repository, InMemoryInventoryRepository):
        init_db()
        with SessionLocal() as db:
            return [_reservation_dict(row) for row in db.query(InventoryReservation).order_by(InventoryReservation.created_at).all()]
    with _LOCK:
        return [dict(item) for item in _RESERVATIONS.values()]


def _reservation_dict(row) -> dict:
    return {"reservation_id": row.reservation_id, "reservation_key": row.reservation_key, "customer_id": row.customer_id, "product_id": row.product_id, "name": next((item["name"] for item in PRODUCTS if item["id"] == row.product_id), row.product_id), "quantity": row.quantity, "pickup_time": row.pickup_time, "status": row.status}


def reserve_product(*, product_id: str, quantity: int, customer_id: str, pickup_time: str, reservation_key: str) -> dict:
    product = next((item for item in PRODUCTS if item["id"] == product_id), None)
    if product is None:
        return {"ok": False, "reason": "PRODUCT_NOT_FOUND", "observed_at": _now()}
    if quantity < 1 or not pickup_time:
        return {"ok": False, "reason": "RESERVATION_FIELDS_REQUIRED", "observed_at": _now()}
    service = get_service()
    if not isinstance(service.repository, InMemoryInventoryRepository):
        init_db()
        with SessionLocal.begin() as db:
            existing = db.get(InventoryReservation, reservation_key)
            if existing:
                return {"ok": True, "data": {**_reservation_dict(existing), "idempotent": True}, "observed_at": _now()}
            inventory = db.get(InventoryState, product_id, with_for_update=True)
            available = max((inventory.on_hand - inventory.reserved), 0) if inventory else 0
            if not inventory or available < quantity:
                return {"ok": False, "reason": "INSUFFICIENT_STOCK", "data": {"product_id": product_id, "name": product["name"], "available_quantity": available, "requested_quantity": quantity}, "observed_at": _now()}
            inventory.reserved += quantity
            reservation = InventoryReservation(reservation_key=reservation_key, reservation_id=uuid4().hex[:12], product_id=product_id, customer_id=customer_id, quantity=quantity, pickup_time=pickup_time, status="RESERVED")
            db.add(reservation)
            return {"ok": True, "data": _reservation_dict(reservation), "observed_at": _now()}
    with _LOCK:
        existing = _RESERVATIONS.get(reservation_key)
        if existing:
            return {"ok": True, "data": {**existing, "idempotent": True}, "observed_at": _now()}
        inventory = get_service().get_current(product_id)
        available = (inventory.get("data") or {}).get("available_quantity") if inventory.get("ok") else 0
        if available is None or available < quantity:
            return {"ok": False, "reason": "INSUFFICIENT_STOCK", "data": {"product_id": product_id, "name": product["name"], "available_quantity": available or 0, "requested_quantity": quantity}, "observed_at": _now()}
        current = inventory["data"]
        service.adjust(product_id, current["on_hand"], current["reserved"] + quantity, reason="CUSTOMER_RESERVATION", actor=customer_id)
        reservation = {"reservation_id": uuid4().hex[:12], "reservation_key": reservation_key, "customer_id": customer_id, "product_id": product_id, "name": product["name"], "quantity": quantity, "pickup_time": pickup_time, "status": "RESERVED"}
        _RESERVATIONS[reservation_key] = reservation
        return {"ok": True, "data": reservation, "observed_at": _now()}
