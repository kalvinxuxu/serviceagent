from backend.app.agent.capability_policy import allowed_tools, is_allowed
from backend.app.agent.contracts import SemanticAction


def test_capability_policy_only_returns_constraints():
    action = SemanticAction(act="REQUOTE")
    assert allowed_tools(action) == {"calculate_order_quote"}


def test_capability_policy_does_not_choose_a_tool_for_state_mutation():
    action = SemanticAction(act="SET_QUANTITY", quantity=3)
    assert is_allowed(action, "calculate_order_quote") is False
    assert allowed_tools(action) == {"edit_selected_items"}
