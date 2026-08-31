from __future__ import annotations

from typing import Any


GOAL_ALIASES = {
    # Semantic Workspace intents are deliberately provider-neutral. Keep this
    # mapping at the boundary so the LLM never needs to know internal goals.
    "ASK_PRICE": "PRICE_CALCULATION", "PRICE_QUERY": "PRICE_CALCULATION",
    "QUERY_PRICE": "PRICE_CALCULATION", "CALCULATE_TOTAL": "PRICE_CALCULATION",
    "ASK_INVENTORY": "INVENTORY_CHECK", "CHECK_INVENTORY": "INVENTORY_CHECK",
    "QUERY": "INVENTORY_CHECK", "INQUIRY": "INVENTORY_CHECK", "AVAILABILITY": "INVENTORY_CHECK",
    "SELECT_PRODUCT": "PRODUCT_SELECTION", "ADD_ITEM": "PRODUCT_SELECTION",
    "SPECIFY_QUANTITY": "PRODUCT_SELECTION", "CHOOSE": "PRODUCT_SELECTION",
    "RECOMMEND": "PRODUCT_RECOMMENDATION", "RECOMMEND_PRODUCTS": "PRODUCT_RECOMMENDATION",
    "COMPARE": "PRODUCT_COMPARE", "COMPARE_PRODUCTS": "PRODUCT_COMPARE",
    "DELIVERY": "SHIPPING_POLICY", "SHIPPING": "SHIPPING_POLICY",
    "AFTER_SALES": "AFTER_SALES",
    "库存": "INVENTORY_CHECK", "查询库存": "INVENTORY_CHECK", "有没有货": "INVENTORY_CHECK",
    "价格": "PRICE_CALCULATION", "计算总价": "PRICE_CALCULATION", "询价": "PRICE_CALCULATION",
    "选择商品": "PRODUCT_SELECTION", "购买": "PRODUCT_SELECTION", "加购": "PRODUCT_SELECTION",
    "推荐": "PRODUCT_RECOMMENDATION", "商品推荐": "PRODUCT_RECOMMENDATION", "推荐商品": "PRODUCT_RECOMMENDATION",
    "浏览商品": "PRODUCT_BROWSE", "商品列表": "PRODUCT_BROWSE",
    "比较价格": "PRODUCT_COMPARE", "价格比较": "PRODUCT_COMPARE",
    "商品适配": "PRODUCT_FIT_QUERY", "适合谁": "PRODUCT_FIT_QUERY",
    "配送": "SHIPPING_POLICY", "邮寄": "SHIPPING_POLICY", "物流": "ORDER_STATUS",
    "优惠": "PROMOTION_QUERY", "会员价": "MEMBERSHIP_PRICING",
    "售后": "AFTER_SALES", "退货": "RETURN", "订单状态": "ORDER_STATUS",
}

KNOWN_GOALS = {
    "ORDER_STATUS", "RETURN", "RECOMMENDATION", "INVENTORY_CHECK", "PRICE_CALCULATION",
    "PRODUCT_BROWSE", "PRODUCT_COMPARE", "PRODUCT_RECOMMENDATION", "PRODUCT_FIT_QUERY", "RESERVATION",
    "SHIPPING_POLICY", "PROMOTION_QUERY", "MEMBERSHIP_PRICING", "FAQ", "PRODUCT_SELECTION",
    "AFTER_SALES", "OTHER",
}


def canonicalize_goal(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    value = value.strip().upper()
    if value in KNOWN_GOALS:
        return value
    for alias, goal in GOAL_ALIASES.items():
        if alias in value or value in alias.upper():
            return goal
    return None


def canonicalize_goals(values: list[Any] | None) -> list[str]:
    result = []
    for value in values or []:
        goal = canonicalize_goal(value)
        if goal and goal not in result:
            result.append(goal)
    return result


def canonicalize_understanding(semantic):
    goals = canonicalize_goals(semantic.goals or semantic.candidate_goals)
    semantic.goals = goals
    semantic.candidate_goals = list(goals)
    return semantic
