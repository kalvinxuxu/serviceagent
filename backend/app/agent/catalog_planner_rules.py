def is_catalog_action(tool_name: str) -> bool:
    return tool_name in {"search_products", "check_inventory", "find_recent_orders", "get_order", "get_order_status"}
