from typing import Any

from pydantic import BaseModel, ConfigDict


class AdminInventoryView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    on_hand: int | None = None
    reserved: int | None = None
    available_quantity: int | None = None
    status: str = "UNKNOWN"


class AdminMediaView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    media_id: str
    url: str
    alt: str = ""


class ProductAdminView(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str
    name: str
    category: str
    dine_in_price: float
    member_price: float | None = None
    promotion_price: float | None = None
    display_discount_price: float | None = None
    inventory: AdminInventoryView
    primary_media: AdminMediaView | None = None
    display_tags: list[str] = []
    featured: bool = False
    status: str = "ON_SALE"
    profile: dict[str, Any] = {}
    aliases: list[str] = []


class ProductAdminListResponse(BaseModel):
    items: list[ProductAdminView]
