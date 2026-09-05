from __future__ import annotations

from typing import Any

from .contracts import ResponseContext


def compose(context: ResponseContext) -> str:
    """Turn already-authorized business facts into a customer-facing reply."""
    result: dict[str, Any] = context.business_result or {}
    if context.action in {"QUOTE", "REQUOTE", "PRICE_CALCULATION"} and result:
        lines = result.get("items", [])
        detail = "；".join(
            f"{item.get('name', '商品')}×{item.get('quantity', 1)}={item.get('subtotal', 0)}元"
            for item in lines
        )
        reply = f"好的，帮您算好了：合计 {result.get('total', 0)} 元"
        if detail:
            reply += f"（{detail}）"
        if result.get("discount", 0):
            reply += f"，已优惠 {result['discount']} 元"
        if result.get("delivery_mode") == "SHIPPING":
            reply += "。如果您需要邮寄，我再帮您确认收货信息和运费"
        else:
            reply += "。当前按到店自取计算。您还需要我帮您看看其他口味吗？"
        return reply
    return str(context.allowed_facts.get("fallback_message", "我来继续帮您处理。"))
