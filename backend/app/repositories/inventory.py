from datetime import datetime
from typing import Protocol

from ..db.models.catalog import InventoryState
from ..db.session import SessionLocal, init_db


class InventoryRepository(Protocol):
    def get_current(self, product_id: str) -> InventoryState | dict | None: ...
    def upsert(self, product_id: str, on_hand: int, reserved: int) -> InventoryState | dict: ...


class SqliteInventoryRepository:
    def get_current(self, product_id: str) -> InventoryState | None:
        init_db()
        with SessionLocal() as db:
            row = db.get(InventoryState, product_id)
            if row is None:
                return None
            return InventoryState(
                product_id=row.product_id, on_hand=row.on_hand, reserved=row.reserved,
                version=row.version, updated_at=row.updated_at,
            )

    def upsert(self, product_id: str, on_hand: int, reserved: int) -> InventoryState:
        if on_hand < 0 or reserved < 0:
            raise ValueError("inventory quantities must be non-negative")
        init_db()
        with SessionLocal() as db:
            row = db.get(InventoryState, product_id)
            if row is None:
                row = InventoryState(product_id=product_id, on_hand=on_hand, reserved=reserved, version=1)
                db.add(row)
            else:
                row.on_hand = on_hand
                row.reserved = reserved
                row.version += 1
                row.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(row)
            return InventoryState(
                product_id=row.product_id, on_hand=row.on_hand, reserved=row.reserved,
                version=row.version, updated_at=row.updated_at,
            )


class InMemoryInventoryRepository:
    """Replaceable test adapter; never used by the running application."""
    def __init__(self, values: dict[str, dict] | None = None):
        self.values = values or {}

    def get_current(self, product_id: str) -> dict | None:
        return self.values.get(product_id)

    def upsert(self, product_id: str, on_hand: int, reserved: int) -> dict:
        self.values[product_id] = {
            "product_id": product_id, "on_hand": on_hand, "reserved": reserved,
            "version": self.values.get(product_id, {}).get("version", 0) + 1,
            "updated_at": datetime.utcnow(),
        }
        return self.values[product_id]
