from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.trace_service import get


def test_turn_persists_component_lineage_and_evaluation():
    state = CustomerServiceState(session_id="lineage_eval_test")
    state, reply, trace = run_turn(state, "原味贝果有货吗")
    assert reply
    assert state.turn_evaluations[-1]["component_scores"]["UNDERSTANDING"] == "PASS"
    steps = get(state.session_id, include_lineage=True)
    components = {step.get("lineage", {}).get("component") for step in steps if step.get("step_type") == "lineage"}
    assert {"UNDERSTANDING", "PLANNER", "PLAN_VALIDATOR", "STATE_MANAGER", "RESPONSE_GENERATION"} <= components
    assert any(step.get("step_type") == "turn_evaluation" for step in steps)
