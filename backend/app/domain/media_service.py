from __future__ import annotations

import hashlib
import os
from pathlib import Path
from uuid import uuid4

from ..db.models.service import ProductAlias, ProductMedia
from ..db.session import SessionLocal, init_db

MEDIA_ROOT = Path(os.getenv("MEDIA_STORAGE_DIR", "data/media"))


def register_media(*, product_id: str | None, asset_type: str, source_path: str, display_name: str, alt_text: str = "") -> dict:
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(source_path)
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    mime = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}.get(path.suffix.lower())
    if not mime:
        raise ValueError("UNSUPPORTED_MEDIA_TYPE")
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    target = MEDIA_ROOT / f"{digest}{path.suffix.lower()}"
    if not target.exists():
        target.write_bytes(path.read_bytes())
    init_db()
    with SessionLocal() as db:
        row = db.query(ProductMedia).filter_by(sha256=digest).first()
        if row is None:
            row = ProductMedia(id=f"MED_{uuid4().hex[:12]}", product_id=product_id, asset_type=asset_type,
                               storage_path=str(target), mime_type=mime, display_name=display_name[:255],
                               alt_text=alt_text[:255], sha256=digest)
            db.add(row)
        elif product_id and row.product_id != product_id:
            row.product_id = product_id
        db.commit()
        return _dump(row)


def _dump(row: ProductMedia) -> dict:
    return {"media_id": row.id, "product_id": row.product_id, "type": row.asset_type,
            "display_name": row.display_name, "alt": row.alt_text, "mime_type": row.mime_type,
            "storage_path": row.storage_path, "status": row.status}


def list_media(product_id: str | None = None, asset_type: str | None = None) -> list[dict]:
    init_db()
    with SessionLocal() as db:
        query = db.query(ProductMedia).filter(ProductMedia.status == "ACTIVE")
        if product_id is not None:
            query = query.filter(ProductMedia.product_id == product_id)
        if asset_type is not None:
            query = query.filter(ProductMedia.asset_type == asset_type)
        return [_dump(row) for row in query.order_by(ProductMedia.sort_order, ProductMedia.created_at).all()]


def get_media(media_id: str) -> dict | None:
    init_db()
    with SessionLocal() as db:
        row = db.get(ProductMedia, media_id)
        return _dump(row) if row and row.status == "ACTIVE" else None


def add_alias(alias: str, product_id: str, alias_type: str = "DISPLAY_NAME", source: str = "MANUAL") -> dict:
    init_db()
    with SessionLocal() as db:
        row = db.query(ProductAlias).filter_by(alias=alias.strip()).first()
        if row is None:
            row = ProductAlias(id=f"ALS_{uuid4().hex[:12]}", alias=alias.strip(), product_id=product_id,
                               alias_type=alias_type, source=source)
            db.add(row)
        else:
            row.product_id = product_id
            row.alias_type = alias_type
            row.source = source
        db.commit()
        return {"alias": row.alias, "product_id": row.product_id, "alias_type": row.alias_type, "source": row.source}


def resolve_alias(query: str) -> str | None:
    normalized = query.strip()
    if not normalized:
        return None
    init_db()
    with SessionLocal() as db:
        row = db.query(ProductAlias).filter_by(alias=normalized).first()
        return row.product_id if row else None
