from ..domain.recommendation_request import canonicalize_recommendation_request


def preference_tags(text: str) -> list[str]:
    return [tag for phrase, tag in (("低糖", "低糖"), ("孩子", "儿童"), ("小朋友", "儿童"), ("儿童", "儿童"), ("老人", "老人"), ("老年人", "老人"), ("长辈", "老人"), ("早餐", "低糖")) if phrase in text]


def recommendation_arguments(text: str, previous: dict | None = None, constraints: dict | None = None, previous_product_ids: list[str] | None = None) -> dict:
    """Build tool arguments from structured semantic constraints and context."""
    args = {"constraints": dict(previous or {})}
    for key, value in (constraints or {}).items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list) and isinstance(args["constraints"].get(key), list):
            args["constraints"][key] = list(dict.fromkeys(args["constraints"][key] + value))
        else:
            args["constraints"][key] = value
    # Quantity and budget extraction are generic request normalization steps.
    # They cover natural phrasing where the number is not immediately after
    # the request verb, e.g. “25块以内给我搭两个不同的面包”.
    import re
    budget_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:块|元)以内", text)
    if "max_price" not in args and not args["constraints"].get("budget") and budget_match:
        args["max_price"] = float(budget_match.group(1))

    generic_categories = {"面包", "食品", "点心", "早餐"}
    if args["constraints"].get("category") in generic_categories:
        args["constraints"].pop("category", None)
    if "不同" in text or "不重复" in text:
        args["constraints"].setdefault("distinct", True)

    if "count" not in args["constraints"] and "quantity" not in args["constraints"] and "count" not in args:
        numbers = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5}
        # Remove the budget number first so “25块以内两个” yields 2.
        quantity_text = re.sub(r"\d+(?:\.\d+)?\s*(?:块|元)以内", "", text)
        matches = re.findall(r"(\d+|一|两|二|三|四|五)\s*(?:个|款)", quantity_text)
        if matches:
            args["count"] = sum(int(value) if value.isdigit() else numbers[value] for value in matches)
        else:
            verb_match = re.search(r"(?:推荐|要|来|想要|给我搭?)\s*(\d+|一|两|二|三|四|五)", quantity_text)
            if verb_match:
                value = verb_match.group(1)
                args["count"] = int(value) if value.isdigit() else numbers[value]
    if args["constraints"]:
        if previous_product_ids:
            args["exclude_product_ids"] = list(previous_product_ids)
        return canonicalize_recommendation_request(args).tool_arguments()
    # Compatibility fallback for offline/mock understanding only. Production
    # DeepSeek output is expected to populate UnderstandingOutput.constraints.
    tags = preference_tags(text)
    if tags:
        args["tags"] = tags
    if "不要儿童" in text or "不含儿童" in text:
        args["exclude_tags"] = ["儿童"]
    if "不喜欢太甜" in text or "不要太甜" in text or "清淡" in text:
        args["exclude_tags"] = ["甜味"]
    if "便宜" in text or "低价" in text:
        args["max_price"] = 15
    import re
    budget = re.search(r"(\d+(?:\.\d+)?)\s*(?:块|元)以内", text)
    if budget:
        args["max_price"] = float(budget.group(1))
    count_match = re.search(r"推荐\s*(\d+|一(?!些)|两|二|三|四|五)?", text)
    if count_match and count_match.group(1):
        raw_count = count_match.group(1)
        args["count"] = int(raw_count) if raw_count.isdigit() else {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5}[raw_count]
    args.setdefault("count", 3)
    categories = [category for category in ("吐司", "贝果", "欧包", "盐面包", "小面包") if category in text]
    if len(categories) > 1:
        args["categories"] = categories
        args.pop("category", None)
    elif categories:
        args["category"] = categories[0]
    else:
        args.setdefault("category", "早餐" if "早餐" in text or not args else None)
    args.setdefault("tags", [])
    if previous_product_ids:
        args["exclude_product_ids"] = list(previous_product_ids)
    return canonicalize_recommendation_request(args).tool_arguments()
