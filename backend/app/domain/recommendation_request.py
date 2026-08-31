from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CanonicalRecommendationRequest(BaseModel):
    constraints: dict[str, Any] = Field(default_factory=dict)
    count: int = Field(default=3, ge=1)
    category: str | None = None
    categories: list[str] = Field(default_factory=list)
    max_price: float | None = None
    exclude_product_ids: list[str] = Field(default_factory=list)

    def tool_arguments(self) -> dict[str, Any]:
        result: dict[str, Any] = {"constraints": self.constraints, "count": self.count}
        if self.category:
            result["category"] = self.category
        if self.categories:
            result["categories"] = self.categories
        if self.max_price is not None:
            result["max_price"] = self.max_price
        if self.exclude_product_ids:
            result["exclude_product_ids"] = self.exclude_product_ids
        return result


def _as_list(value: Any) -> list[Any]:
    if value in (None, "", [], {}):
        return []
    return value if isinstance(value, list) else [value]


def _canonical_sweetness(value: Any) -> Any:
    if value is None:
        return None
    text = str(value).strip()
    return {"low": "LOW", "normal": "NORMAL", "high": "HIGH", "低糖": "LOW", "不甜": "LOW", "不太甜": "LOW", "普通": "NORMAL", "偏甜": "HIGH"}.get(text.lower(), text.upper())


def canonicalize_recommendation_request(raw: dict[str, Any] | None) -> CanonicalRecommendationRequest:
    raw = dict(raw or {})
    constraints = dict(raw.get("constraints") or {})
    for key, value in raw.items():
        if key not in {"constraints", "count", "quantity", "category", "categories", "max_price", "budget", "exclude_product_ids"} and value not in (None, "", [], {}):
            constraints.setdefault(key, value)
    category_value = raw.get("category", constraints.pop("category", None))
    if isinstance(category_value, str) and category_value in {"面包", "食品", "点心", "早餐"}:
        category_value = None
    categories = _as_list(raw.get("categories", constraints.pop("categories", None)))
    if isinstance(category_value, list):
        categories = categories or category_value
        category_value = None
    categories = list(dict.fromkeys(str(item) for item in categories if item))
    if len(categories) == 1 and category_value is None:
        category_value, categories = categories[0], []
    explicit_count = raw.get("count", constraints.pop("count", None))
    quantity = raw.get("quantity", constraints.pop("quantity", None))
    count = explicit_count or quantity or (len(categories) if categories else 3)
    try:
        count = int(count)
    except (TypeError, ValueError):
        count = len(categories) if categories else 3
    if categories and explicit_count is None and quantity is None:
        count = len(categories)
    if len(categories) > 1 and count < len(categories):
        count = len(categories)
    if "sweetness" in constraints:
        constraints["sweetness"] = _canonical_sweetness(constraints["sweetness"])
    budget = raw.get("max_price", raw.get("budget", constraints.pop("budget", None)))
    try:
        budget = float(budget) if budget is not None else None
    except (TypeError, ValueError):
        budget = None
    return CanonicalRecommendationRequest(
        constraints=constraints,
        count=max(1, count),
        category=category_value,
        categories=categories,
        max_price=budget,
        exclude_product_ids=list(raw.get("exclude_product_ids") or constraints.pop("exclude_product_ids", [])),
    )
