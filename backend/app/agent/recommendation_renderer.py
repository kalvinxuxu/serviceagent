def render(products: list[dict], constraints: dict | None = None) -> str:
    constraints = constraints or {}
    semantic_constraints = constraints.get("constraints", constraints)
    audience_values = semantic_constraints.get("audience", [])
    audience_values = audience_values if isinstance(audience_values, list) else [audience_values]
    if not products:
        if semantic_constraints.get("sweetness") not in (None, "LOW", "NORMAL", "HIGH"):
            return "我理解您想要清淡一些的口味，但店内资料里暂时没有足够明确的对应标注。我可以按低糖、原味或咸香口味再帮您筛一遍，您更偏向哪一种呢？"
        if semantic_constraints.get("sweetness") == "LOW":
            return "目前同时满足您说的人群和低甜要求的现货不多。如果甜度条件稍微放宽，我可以再为您推荐几款。"
        return "我按您刚才说的口味和人群看了一下，暂时没有特别合适且有货的款式。您愿意放宽哪一项条件，我再继续帮您筛选？"
    audience = audience_values[0] if audience_values else None
    if audience == "儿童":
        audience = "小朋友"
    elif audience in {"老人", "SENIOR", "ELDERLY"}:
        audience = "老人家"
    elif audience in {"CHILD", "child"}:
        audience = "小朋友"
    refinement = bool(semantic_constraints.get("texture") or semantic_constraints.get("flavor") or semantic_constraints.get("sweetness")) and bool(constraints.get("exclude_product_ids"))
    if refinement:
        opening = "明白，您想把口感或风味再收窄一些。我从刚才的范围里重新筛了一遍，比较推荐："
    elif audience:
        opening = f"如果是给家里{audience}吃，我会优先考虑口味温和、接受度高的这几款："
    elif semantic_constraints.get("sweetness") == "LOW" or "甜味" in constraints.get("exclude_tags", []):
        opening = "如果您不想要太甜的，我会更建议从咸香、原味或低糖的款式里选："
    else:
        opening = "我帮您挑了几款目前有货、比较适合的："
    items = []
    for product in products:
        matched = product.get("matched_features", [])
        points = product.get("selling_points", [])[:2]
        detail = "、".join(points) if points else ("符合" + "、".join(matched[:2]) if matched else product.get("category", "面包"))
        items.append(f"{product['name']}（{product['price']}元，{detail}）")
    closing = "这些都是现货，您可以按口味挑选；如果您告诉我更偏好软一点、咸一点还是低糖，我还可以继续帮您缩小范围。"
    return opening + "；".join(items) + "。" + closing
