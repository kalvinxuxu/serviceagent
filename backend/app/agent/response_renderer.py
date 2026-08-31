def render_inventory(data: dict) -> str:
    if data.get("inventory_status") == "UNKNOWN":
        return f"暂时无法确认{data['name']}的实时库存，建议转人工处理。"
    return f"{data['name']}目前{'有货' if data['available'] else '缺货'}，可售库存 {data['available_quantity']} 件。"

def render_order(data: dict) -> str:
    return f"订单 {data['id']} 当前状态：{data['status']}。"
