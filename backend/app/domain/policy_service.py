POLICIES = {"return": {"days": 7, "text": "签收后7天内可申请退货"}, "shipping": {"text": "物流状态以查询结果为准"}}

def search(query: str) -> dict | None:
    q = query.lower()
    if "退" in q or "换" in q: return POLICIES["return"]
    if "物流" in q or "到" in q: return POLICIES["shipping"]
    return None
