from __future__ import annotations

import base64
import hashlib
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from ..db.models.service import EvidenceAttachment
from ..db.session import SessionLocal, init_db
from ..domain.catalog import ORDERS
from ..llm.multimodal import MultimodalEvidenceAdapter


IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


def _retention_days() -> int:
    try:
        return max(int(os.getenv("IMAGE_RETENTION_DAYS", "180")), 1)
    except ValueError:
        return 180


def _redact(value: str | None) -> str | None:
    if not value:
        return value
    if len(value) <= 8:
        return "***"
    return value[:4] + "***" + value[-4:]


def _candidate_from_facts(observation: dict) -> dict:
    def first_value(*keys):
        for key in keys:
            value = observation.get(key)
            if value:
                return value
        return None

    facts = observation.get("observed_facts", [])
    if isinstance(facts, str):
        facts = [facts]
    extra_text = []
    for key in ("observed_elements", "text", "raw_text", "description", "address", "extracted_address"):
        value = observation.get(key)
        if value:
            extra_text.extend(value if isinstance(value, list) else [value])
    facts_text = " ".join(str(item) for item in [*facts, *extra_text])

    address = first_value("address_candidate", "extracted_address", "address")
    if not address:
        address_match = re.search(
            r"([一-鿿]{2,}(?:省|自治区|市)[^。；;\n]{2,80}(?:号|栋|幢|室|单元|花园|小区)[^。；;\n]{0,30})",
            facts_text,
        )
        address = address_match.group(1).strip(" ：:，,。") if address_match else None

    tracking = first_value("tracking_number_candidate", "tracking_number", "waybill_number")
    if not tracking:
        match = re.search(r"(?i)(?:SF|顺丰)?[A-Z0-9]{8,20}", facts_text)
        tracking = match.group(0) if match else None
    return {
        "address_candidate": address,
        "order_id_candidate": first_value("order_id_candidate", "order_id", "order_number"),
        "tracking_number_candidate": tracking,
    }


def save_attachment(session_id: str, filename: str, mime_type: str, content: bytes) -> dict:
    if mime_type not in IMAGE_TYPES:
        raise ValueError("UNSUPPORTED_IMAGE_TYPE")
    if len(content) > 10 * 1024 * 1024:
        raise ValueError("IMAGE_TOO_LARGE")
    attachment_id = f"ATT_{uuid4().hex[:12]}"
    digest = hashlib.sha256(content).hexdigest()
    root = Path(os.getenv("EVIDENCE_STORAGE_DIR", "data/evidence"))
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{attachment_id}.bin"
    path.write_bytes(content)
    created = datetime.utcnow()
    init_db()
    with SessionLocal() as db:
        db.add(EvidenceAttachment(
            id=attachment_id,
            conversation_id=session_id,
            filename=filename[:255],
            mime_type=mime_type,
            storage_path=str(path),
            sha256=digest,
            expires_at=created + timedelta(days=_retention_days()),
        ))
        db.commit()
    return {"attachment_id": attachment_id, "filename": filename, "mime_type": mime_type, "sha256": digest, "path": str(path)}


def observe_attachment(attachment: dict) -> dict:
    data = Path(attachment["path"]).read_bytes()
    data_url = f"data:{attachment['mime_type']};base64,{base64.b64encode(data).decode()}"
    observation = MultimodalEvidenceAdapter().observe({
        "data_url": data_url,
        "filename": attachment["filename"],
        "attachment_id": attachment["attachment_id"],
    })
    if hasattr(observation, "model_dump"):
        observation = observation.model_dump()
    observation = dict(observation or {})
    observation.update(_candidate_from_facts(observation))
    observation["evidence_id"] = observation.get("evidence_id") or f"EV_{uuid4().hex[:12]}"
    observation["attachment_ids"] = [attachment["attachment_id"]]
    classification = str(observation.get("classification", "UNKNOWN_VISUAL_ISSUE")).upper()
    classification_aliases = {
        "DELIVERY_ADDRESS": "ADDRESS", "ADDRESS_INFO": "ADDRESS", "地址": "ADDRESS",
        "ORDER_NUMBER": "ORDER_REFERENCE", "订单号": "ORDER_REFERENCE",
        "TRACKING_NUMBER": "TRACKING_REFERENCE", "WAYBILL": "TRACKING_REFERENCE", "快递单号": "TRACKING_REFERENCE",
    }
    classification = classification_aliases.get(classification, classification)
    if classification in {"DAMAGED_PRODUCT", "QUALITY_RISK", "FOOD_SAFETY_RISK", "PACKAGING_DAMAGE", "PRODUCT_DAMAGE", "QUALITY_DEFECT"}:
        observation["classification"] = classification
    elif observation.get("address_candidate"):
        observation["classification"] = "ADDRESS"
    elif observation.get("order_id_candidate"):
        observation["classification"] = "ORDER_REFERENCE"
    elif observation.get("tracking_number_candidate"):
        observation["classification"] = "TRACKING_REFERENCE"
    else:
        observation["classification"] = classification or "UNKNOWN_VISUAL_ISSUE"
    return observation


def match_order(observation: dict, customer_id: str | None) -> dict:
    candidate = observation.get("order_id_candidate") or observation.get("tracking_number_candidate")
    matches = []
    for order in ORDERS.values():
        if candidate and candidate in {order.get("id"), order.get("tracking_number")}:
            matches.append(order)
    if len(matches) != 1:
        return {"match_status": "NOT_UNIQUE", "authorized": False, "candidate": _redact(candidate)}
    order = matches[0]
    authorized = bool(customer_id and order.get("customer_id") == customer_id)
    return {
        "match_status": "MATCHED",
        "authorized": authorized,
        "order_id": order["id"] if authorized else None,
        "tracking_number": _redact(order.get("tracking_number") or candidate) if authorized else None,
        "authorization_status": "AUTHORIZED" if authorized else "DENIED",
    }


def simulated_logistics(order_id: str) -> dict:
    order = ORDERS.get(order_id)
    if not order:
        return {"ok": False, "reason": "ORDER_NOT_FOUND"}
    return {"ok": True, "data": {
        "tracking_number": _redact(order.get("tracking_number") or f"SF{order_id[-6:]}"),
        "carrier": "SF",
        "status": "IN_TRANSIT" if order.get("status") == "运输中" else "DELIVERED",
        "status_text": order.get("status", "未知"),
        "latest_event": {"description": order.get("status", "暂无最新物流记录"), "occurred_at": datetime.utcnow().isoformat()},
        "queried_at": datetime.utcnow().isoformat(),
    }}
