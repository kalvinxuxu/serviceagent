from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from ..domain.media_service import get_media, list_media

router = APIRouter(prefix="/api/v1/media")


@router.get("/{media_id}")
def serve_media(media_id: str):
    media = get_media(media_id)
    if not media:
        raise HTTPException(status_code=404, detail="MEDIA_NOT_FOUND")
    path = Path(media["storage_path"]).resolve()
    if not path.is_file():
        raise HTTPException(status_code=404, detail="MEDIA_FILE_NOT_FOUND")
    return FileResponse(path, media_type=media["mime_type"], filename=media["display_name"])


@router.get("")
def media_list(product_id: str | None = None, asset_type: str | None = None):
    return {"items": list_media(product_id, asset_type)}
