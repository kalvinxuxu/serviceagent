CAPABILITIES = {
    "RETURN": {"find_recent_orders", "get_order", "check_return_eligibility", "create_return_request", "search_policy"},
    "INVENTORY_CHECK": {"search_products", "check_inventory", "list_available_inventory", "check_selected_items_inventory"},
    "PRICE_CALCULATION": {"calculate_order_quote", "edit_selected_items"},
    "RECOMMENDATION": {"recommend_products", "search_products"},
    "PRODUCT_BROWSE": {"list_available_inventory"},
    "PRODUCT_COMPARE": {"compare_products"},
    "PRODUCT_FIT_QUERY": {"explain_product_fit"},
    "PRODUCT_RECOMMENDATION": {"recommend_products", "search_products"},
    "SHIPPING_POLICY": {"calculate_order_quote"},
    "PROMOTION_QUERY": {"get_sales_policy"},
    "MEMBERSHIP_PRICING": {"calculate_order_quote"},
    "FAQ": {"answer_store_faq"},
    "RESERVATION": {"check_inventory", "reserve_product"},
    "ORDER_STATUS": {"find_recent_orders", "get_order", "get_order_status", "match_order_from_evidence", "query_logistics_status"},
    "OTHER": set(),
}


def resolve_capabilities(goal_type: str) -> list[str]:
    return sorted(CAPABILITIES.get(goal_type, set()))
