def normalize(text: str) -> dict:
    result = {"tags": [], "category": "早餐" if "早餐" in text else None, "max_price": None}
    if "低糖" in text: result["tags"].append("低糖")
    if "孩子" in text or "儿童" in text: result["tags"].append("儿童")
    return result
