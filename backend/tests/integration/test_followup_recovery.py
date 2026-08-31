import os

from backend.app.agent.contracts import PendingFollowup
from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState


def test_affirmative_reply_restores_recommendation_and_clears_pending():
    os.environ["LLM_PROVIDER"] = "mock"
    state = CustomerServiceState(
        session_id="followup-recovery-test",
        pending_followup=PendingFollowup(
            type="RECOMMEND_PRODUCTS", source_turn_id="followup-recovery-test:1", prompt="继续推荐",
            constraints={"audience": "儿童"}
        ),
    )
    state, reply, trace = run_turn(state, "好的")
    assert reply
    assert trace["next_action"].get("tool_name") == "recommend_products"
    assert state.pending_followup is None
    assert state.known_facts["recommendation_constraints"].get("constraints", {}).get("audience") == "儿童"


def test_rejected_followup_is_closed_without_tool_execution():
    state = CustomerServiceState(session_id="followup-reject-test", pending_followup=PendingFollowup(
        type="RECOMMEND_PRODUCTS", source_turn_id="reject:1", prompt="继续推荐", constraints={"audience": "儿童"}
    ))
    state, reply, trace = run_turn(state, "不用")
    assert reply
    assert trace["next_action"].get("tool_name") is None
    assert state.pending_followup is None


def test_standalone_affirmative_reply_is_clarified_safely():
    state, reply, trace = run_turn(CustomerServiceState(session_id="standalone-affirm-test"), "好的")
    assert reply
    assert trace["next_action"]["type"] == "ASK_USER"
    assert trace["next_action"].get("tool_name") is None
