from .contracts import PolicyDecision


READ_ONLY_TOOLS = {
    "check_inventory",
    "check_selected_items_inventory",
    "list_available_inventory",
    "search_products",
    "compare_products",
    "calculate_order_quote",
    "get_sales_policy",
    "answer_store_faq",
}
DENIED_TOOLS = {"delete_customer_data", "refund_without_confirmation"}


def decide(tool_name: str | None, *, confirmed: bool = False) -> PolicyDecision:
    """Apply risk/confirmation policy; never choose or rewrite a capability."""
    if not tool_name or tool_name in READ_ONLY_TOOLS:
        return PolicyDecision(decision="ALLOW", reason_code="READ_ONLY")
    if tool_name in DENIED_TOOLS:
        return PolicyDecision(decision="DENY", reason_code="FORBIDDEN_SIDE_EFFECT")
    if tool_name == "create_return_request" and not confirmed:
        return PolicyDecision(decision="REQUIRE_CONFIRMATION", reason_code="SIDE_EFFECT")
    return PolicyDecision(decision="ALLOW" if confirmed else "ESCALATE", reason_code="SIDE_EFFECT")
