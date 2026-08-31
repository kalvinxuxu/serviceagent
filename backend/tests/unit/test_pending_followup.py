from backend.app.agent.state import CustomerServiceState
from backend.app.agent.contracts import PendingFollowup


def test_pending_followup_round_trips_in_state():
    state = CustomerServiceState(session_id="pending-test", pending_followup=PendingFollowup(
        type="RECOMMEND_PRODUCTS", source_turn_id="pending-test:1", prompt="继续推荐", constraints={"audience": "儿童"}
    ))
    restored = CustomerServiceState.model_validate(state.model_dump())
    assert restored.pending_followup.constraints["audience"] == "儿童"
