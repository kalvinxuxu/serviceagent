from backend.app.agent.state import CustomerServiceState
from backend.app.agent.turn_evaluator import evaluate_turn


def test_invalid_understanding_marks_downstream_steps_not_run():
    state = CustomerServiceState(session_id="eval-failure-test")
    state.known_facts["understanding_status"] = "VALID"
    evaluation = evaluate_turn(state, {
        "reason_code": "LLM_OUTPUT_INVALID",
        "next_action": {"type": "ASK_USER", "arguments": {}},
    })
    assert evaluation.failure_component == "UNDERSTANDING"
    assert evaluation.component_scores["PLANNER"] == "NOT_RUN"
    assert evaluation.component_scores["BUSINESS_SERVICE"] == "NOT_RUN"
    assert evaluation.component_scores["RESPONSE_GENERATION"] == "FAIL"
