from __future__ import annotations

from typing import Any

from .contracts import ClarificationRequest, MissingSlot


CAPABILITY_SLOTS: dict[str, tuple[MissingSlot, ...]] = {
    "SELECT_PRODUCT": (
        MissingSlot(name="quantity", prompt="您需要几个呢？", priority=1),
    ),
    "CREATE_DELIVERY_REQUEST": (
        MissingSlot(name="delivery_address", prompt="可以的，我们支持面包寄送。为了确认配送范围和运费，请先告诉我收货城市和详细地址。", priority=1, sensitive=True),
        MissingSlot(name="recipient_name", prompt="请提供收货人姓名。", priority=2),
        MissingSlot(name="phone", prompt="请提供收货人联系电话。", priority=3, sensitive=True),
    ),
}


def missing_slots(capability: str, known: dict[str, Any] | None = None) -> list[MissingSlot]:
    known = known or {}
    return [slot for slot in CAPABILITY_SLOTS.get(capability, ()) if known.get(slot.name) in (None, "", [], {})]


def next_clarification(capability: str, known: dict[str, Any] | None = None) -> ClarificationRequest | None:
    missing = missing_slots(capability, known)
    if not missing:
        return None
    return ClarificationRequest(capability=capability, missing_slots=missing, next_slot=missing[0].name)
