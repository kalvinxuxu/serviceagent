from itertools import combinations, product as cartesian_product

from .catalog import PRODUCTS
from .inventory_service import get_service
from .media_service import list_media
from .business_config import FEATURED_LIST


def _as_list(value):
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def normalize_constraints(raw: dict | None) -> dict:
    constraints = dict(raw or {})
    for key in ("audience", "texture", "flavor", "nutrition", "exclude", "categories", "exclude_categories"):
        constraints[key] = _as_list(constraints.get(key))
    aliases = {
        "小朋友": "儿童",
        "小孩": "儿童",
        "小孩儿": "儿童",
        "孩子": "儿童",
        "CHILD": "儿童",
        "老年人": "老人",
        "老人家": "老人",
        "长辈": "老人",
        "elderly": "老人",
        "SENIOR": "老人",
        "软": "柔软",
        "松软一些": "松软",
        "咸": "咸香",
    }
    for key in ("audience", "texture", "flavor", "nutrition", "exclude"):
        constraints[key] = [aliases.get(value, value) for value in constraints[key]]
    if isinstance(constraints.get("category"), list):
        constraints["categories"] = constraints.pop("category")
    elif isinstance(constraints.get("categories"), str):
        constraints["categories"] = [constraints["categories"]]
    sweetness = constraints.get("sweetness")
    if isinstance(sweetness, str):
        constraints["sweetness"] = {"low": "LOW", "normal": "NORMAL", "high": "HIGH", "低糖": "LOW", "不太甜": "LOW"}.get(sweetness.strip().lower(), sweetness.upper())
    return constraints

def recommend(tags: list[str] | None = None, category: str | None = None, max_price: float | None = None, exclude_tags: list[str] | None = None, categories: list[str] | None = None, count: int = 3, constraints: dict | None = None, exclude_product_ids: list[str] | None = None) -> list[dict]:
    tags = tags or []
    exclude_tags = exclude_tags or []
    constraints = normalize_constraints(constraints)
    exclude_product_ids = set(exclude_product_ids or constraints.get("exclude_product_ids", []))
    tags = list(dict.fromkeys(tags + constraints.get("nutrition", []) + constraints.get("audience", [])))
    exclude_tags = list(dict.fromkeys(exclude_tags + constraints.get("exclude", [])))
    category = category or constraints.get("category")
    max_price = max_price if max_price is not None else constraints.get("budget")
    categories = categories or constraints.get("categories")
    excluded_categories = set(constraints.get("exclude_categories", []))
    preferred_texture = set(constraints.get("texture", []))
    preferred_flavor = set(constraints.get("flavor", []))
    sweetness = constraints.get("sweetness")
    candidates = []
    for product in PRODUCTS:
        data = get_service().get_current(product["id"]).get("data", {})
        if (data.get("available_quantity") or 0) <= 0 or product["id"] in exclude_product_ids:
            continue
        if (category and product["category"] != category) or (categories and product["category"] not in categories) or product["category"] in excluded_categories or (max_price and product["price"] > max_price):
            continue
        searchable_tags = set(product.get("tags", [])) | set(product.get("audience_tags", [])) | set(product.get("nutrition_tags", []))
        if not all(t in searchable_tags for t in tags) or any(t in searchable_tags for t in exclude_tags):
            continue
        if sweetness not in (None, "LOW", "NORMAL", "HIGH"):
            continue
        if sweetness == "LOW" and "低糖" not in searchable_tags:
            continue
        matched_features = []
        if category or categories:
            matched_features.append("CATEGORY_MATCH")
        if sweetness == "LOW":
            matched_features.append("LOW_SWEETNESS")
        if preferred_texture & set(product.get("texture_tags", [])):
            matched_features.append("TEXTURE_MATCH")
        if preferred_flavor & set(product.get("flavor_tags", [])):
            matched_features.append("FLAVOR_MATCH")
        if set(tags) & (set(product.get("audience_tags", [])) | set(product.get("tags", []))):
            matched_features.append("AUDIENCE_MATCH")
        candidates.append({**product, **{k: data[k] for k in ("inventory_status", "on_hand", "reserved", "available_quantity", "available")},
                           "matched_features": matched_features, "media": list_media(product["id"])})
    def rank(product_item):
        texture_score = len(preferred_texture & set(product_item.get("texture_tags", [])))
        flavor_score = len(preferred_flavor & set(product_item.get("flavor_tags", [])))
        tag_score = len(set(tags) & (set(product_item.get("tags", [])) | set(product_item.get("audience_tags", []))))
        featured_rank = FEATURED_LIST.get("product_ids", []).index(product_item["id"]) if product_item["id"] in FEATURED_LIST.get("product_ids", []) else 999
        return (-(texture_score * 4 + flavor_score * 2 + tag_score), featured_rank, product_item["price"])
    ordered = sorted(candidates, key=rank)
    if not categories:
        return ordered[:count]
    count = len(categories)
    groups = [[item for item in ordered if item["category"] == current] for current in categories]
    for combination in cartesian_product(*groups):
        if len({item["id"] for item in combination}) < len(combination):
            continue
        if max_price is None or sum(item["price"] for item in combination) <= max_price:
            return list(combination)
    return []


def relaxation_options(constraints: dict | None = None) -> list[dict]:
    constraints = normalize_constraints(constraints)
    options = []
    if constraints.get("sweetness") == "LOW":
        options.append({"constraint": "sweetness", "effect": "放宽甜度条件后可增加候选商品"})
    if constraints.get("texture"):
        options.append({"constraint": "texture", "effect": "放宽口感条件后可增加候选商品"})
    if constraints.get("audience"):
        options.append({"constraint": "audience", "effect": "放宽适用人群后可增加候选商品"})
    return options
