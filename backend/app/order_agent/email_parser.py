import re
from .repositories import now

_ITEM = re.compile(r"([\u4e00-\u9fffA-Za-z0-9（）()· -]{2,}?)[：:]?\s*(\d+(?:\.\d+)?)\s*(个|件|只|盒|袋|份|kg|公斤)?")

def parse_email(subject: str, body: str, sender: str) -> dict:
    text = f"{subject}\n{body}"
    order_intent = bool(re.search(r"订|订单|购买|要货|采购|下单|order|purchase", text, re.I))
    items = []
    for match in _ITEM.finditer(body):
        raw = match.group(1).strip(" ，,。；;\n")
        if raw in {"明天", "下午", "数量", "公司", "我要", "请给我"} or len(raw) > 30:
            continue
        items.append({"item_id": f"item_{len(items)+1}", "raw_description": raw, "product_name": raw, "requested_quantity": float(match.group(2)), "unit": match.group(3) or "个", "match_status": "UNRESOLVED", "field_confidence": 0.9})
    missing = []
    if not items: missing.append("items")
    if not re.search(r"地址|送到|配送|公司|门店|address|deliver|company", body, re.I): missing.append("delivery.address")
    if not re.search(r"明天|今天|后天|tomorrow|today|\d{1,2}月\d{1,2}[日号]?", body, re.I): missing.append("delivery.date")
    return {"classification": "ORDER" if order_intent else "NON_ORDER", "customer": {"email": sender}, "items": items, "delivery": {"raw": body}, "missing_information": missing, "conflicts": [], "observed_at": now()}
