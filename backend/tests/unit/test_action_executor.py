from backend.app.agent.action_mapping import atomic_decision
from backend.app.agent.contracts import SemanticAction
from backend.app.agent.executor import ActionExecutor


def test_atomic_query_maps_to_one_tool_without_goal_logic():
    decision = atomic_decision(SemanticAction(act="QUERY", goal=None), arguments={"product_id": "SKU001"})
    assert decision.tool_name == "check_inventory"
    assert decision.action == "QUERY"


def test_state_mutation_has_no_tool_call():
    decision = atomic_decision(SemanticAction(act="SET_QUANTITY", quantity=3))
    assert decision.kind == "STATE_MUTATION"
    assert decision.tool_name is None


def test_executor_returns_standard_tool_result():
    decision = atomic_decision(SemanticAction(act="QUERY"), arguments={"product_id": "SKU001"})
    result = ActionExecutor().execute(decision)
    assert hasattr(result, "ok")
