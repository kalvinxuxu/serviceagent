from __future__ import annotations

from .contracts import SemanticAction

# This is a constraint catalogue, not a second planner. It never chooses the
# tool; the action executor receives the action and performs that mapping.
ACTION_CAPABILITIES: dict[str, frozenset[str]] = {
    "BROWSE": frozenset({"list_available_inventory"}),
    # Legacy planner may classify a category-level inventory browse as QUERY;
    # keep the canonical list tool available without adding a second planner.
    "QUERY": frozenset({"check_inventory", "search_products", "list_available_inventory"}),
    "SELECT": frozenset({"edit_selected_items"}),
    "ADD": frozenset({"edit_selected_items"}),
    "REMOVE": frozenset({"edit_selected_items"}),
    "SET_QUANTITY": frozenset({"edit_selected_items"}),
    "REPLACE": frozenset({"edit_selected_items"}),
    "KEEP": frozenset(),
    "COMPARE": frozenset({"compare_products"}),
    "REQUOTE": frozenset({"calculate_order_quote"}),
}


def allowed_tools(action: SemanticAction | str) -> set[str]:
    key = action.act if isinstance(action, SemanticAction) else str(action)
    return set(ACTION_CAPABILITIES.get(key, frozenset()))


def is_allowed(action: SemanticAction | str, tool_name: str) -> bool:
    return tool_name in allowed_tools(action)
