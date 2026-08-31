from __future__ import annotations

from copy import deepcopy
from uuid import uuid4

from ..db.models.service import CustomerMemory
from ..db.session import SessionLocal, init_db

ALLOWED_TYPES = {"EXPLICIT_PREFERENCE", "EXPLICIT_AVOIDANCE", "CONFIRMED_CONTEXT", "OBSERVED_BEHAVIOR"}


def read(customer_id: str | None) -> list[dict]:
    if not customer_id:
        return []
    init_db()
    with SessionLocal() as db:
        rows = db.query(CustomerMemory).filter_by(customer_id=customer_id, status="ACTIVE").all()
        return [_dump(row) for row in rows]


def validate_candidate(candidate: dict) -> tuple[bool, str | None]:
    if candidate.get("type") not in ALLOWED_TYPES:
        return False, "MEMORY_TYPE_NOT_ALLOWED"
    if candidate.get("type") != "OBSERVED_BEHAVIOR" and not candidate.get("explicit", False) and candidate.get("source") != "USER_EXPLICIT":
        return False, "MEMORY_REQUIRES_EXPLICIT_USER_SIGNAL"
    if not candidate.get("key") or candidate.get("value") in (None, "", [], {}):
        return False, "MEMORY_VALUE_REQUIRED"
    return True, None


def write(customer_id: str, candidate: dict) -> dict:
    valid, reason = validate_candidate(candidate)
    if not valid:
        return {"ok": False, "reason": reason}
    init_db()
    with SessionLocal() as db:
        row = db.query(CustomerMemory).filter_by(customer_id=customer_id, memory_key=candidate["key"], status="ACTIVE").first()
        if row is None:
            row = CustomerMemory(id=f"MEM_{uuid4().hex[:12]}", customer_id=customer_id,
                                 memory_type=candidate["type"], memory_key=candidate["key"],
                                 memory_value={"value": candidate["value"]}, source=candidate.get("source", "USER_EXPLICIT"),
                                 confidence=float(candidate.get("confidence", 1.0)), confirmed=True)
            db.add(row)
        else:
            row.memory_type = candidate["type"]
            row.memory_value = {"value": candidate["value"]}
            row.source = candidate.get("source", "USER_EXPLICIT")
            row.confidence = float(candidate.get("confidence", 1.0))
            row.confirmed = True
        db.commit()
        return {"ok": True, "data": _dump(row)}


def remove(customer_id: str, key: str) -> bool:
    init_db()
    with SessionLocal() as db:
        rows = db.query(CustomerMemory).filter_by(customer_id=customer_id, memory_key=key, status="ACTIVE").all()
        for row in rows:
            row.status = "DELETED"
        db.commit()
        return bool(rows)


def _dump(row: CustomerMemory) -> dict:
    return {"id": row.id, "customer_id": row.customer_id, "type": row.memory_type,
            "key": row.memory_key, "value": deepcopy(row.memory_value.get("value")),
            "source": row.source, "confidence": row.confidence, "confirmed": bool(row.confirmed)}
