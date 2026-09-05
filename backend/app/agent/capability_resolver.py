from .capability_policy import allowed_tools


# Legacy goal names remain supported at this boundary. Converged runtime code
# uses action names and asks capability_policy for constraints only.
GOAL_TO_ACTION = {
    "INVENTORY_CHECK": "QUERY",
    "PRODUCT_BROWSE": "BROWSE",
    "PRODUCT_COMPARE": "COMPARE",
    "PRICE_CALCULATION": "REQUOTE",
}

CAPABILITIES = {
    "RETURN": {"find_recent_orders", "get_order", "check_return_eligibility", "create_return_request", "search_policy"},
    # Keep both legacy goal spellings on the same capability contract.
    "RECOMMENDATION": {"recommend_products", "search_products"},
    "PRODUCT_RECOMMENDATION": {"recommend_products", "search_products"},
    "PRODUCT_FIT_QUERY": {"explain_product_fit"},
    "SHIPPING_POLICY": {"calculate_order_quote"},
    "PROMOTION_QUERY": {"get_sales_policy"},
    "MEMBERSHIP_PRICING": {"calculate_order_quote"},
    "FAQ": {"answer_store_faq"},
    "RESERVATION": {"check_inventory", "reserve_product"},
    "ORDER_STATUS": {"find_recent_orders", "get_order", "get_order_status", "match_order_from_evidence", "query_logistics_status"},
    "OTHER": set(),
}


def resolve_capabilities(goal_type: str) -> list[str]:
    action = GOAL_TO_ACTION.get(goal_type)
    if action:
        return allowed_tools(action)
    return sorted(CAPABILITIES.get(goal_type, set()))
