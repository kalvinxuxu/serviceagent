from backend.app.agent.contracts import PendingFollowup
from backend.app.agent.state import CustomerServiceState


def test_converged_state_round_trips_business_context_without_promoting_focus():
    state = CustomerServiceState(
        session_id="state-contract",
        focused_product={"product_id": "SKU001", "name": "原味贝果"},
        pending_followup=PendingFollowup(
            type="RECOMMEND_PRODUCTS",
            source_turn_id="state-contract:1",
            prompt="继续推荐",
            constraints={"audience": "儿童"},
        ),
    )
    restored = CustomerServiceState.model_validate(state.model_dump(mode="json"))
    assert restored.focused_product["product_id"] == "SKU001"
    assert restored.known_facts.get("selected_products", []) == []
    assert restored.pending_followup.constraints == {"audience": "儿童"}
