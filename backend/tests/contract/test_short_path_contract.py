import pytest

from backend.app.agent.action_mapping import atomic_decision
from backend.app.agent.contracts import SemanticAction


@pytest.mark.parametrize(
    ("action", "tool"),
    [
        ("BROWSE", "list_available_inventory"),
        ("QUERY", "check_inventory"),
        ("COMPARE", "compare_products"),
        ("REQUOTE", "calculate_order_quote"),
    ],
)
def test_atomic_action_has_one_explicit_capability(action, tool):
    decision = atomic_decision(SemanticAction(act=action))
    assert decision.kind == "TOOL_CALL"
    assert decision.tool_name == tool


def test_state_mutation_action_does_not_select_a_tool():
    decision = atomic_decision(SemanticAction(act="SET_QUANTITY", quantity=3), arguments={"quantity": 3})
    assert decision.kind == "STATE_MUTATION"
    assert decision.tool_name is None
