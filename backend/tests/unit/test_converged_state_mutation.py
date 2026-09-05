from backend.app.agent.state import CustomerServiceState
from backend.app.agent.state_mutation import apply_action


def test_set_quantity_does_not_duplicate_items():
    state = CustomerServiceState(
        session_id="mutation-quantity",
        known_facts={"selected_products": [{"product_id": "SKU022", "name": "原味贝果", "quantity": 2}]},
    )
    result = apply_action(state, "SET_QUANTITY", {"resolved_product_ids": ["SKU022"]}, 3)
    assert result["status"] == "PASS"
    assert state.known_facts["selected_products"] == [{"product_id": "SKU022", "name": "原味贝果", "quantity": 3}]


def test_ambiguous_reference_has_no_mutation():
    state = CustomerServiceState(
        session_id="mutation-ambiguous",
        known_facts={"selected_products": [{"product_id": "SKU022", "quantity": 1}]},
    )
    result = apply_action(state, "SET_QUANTITY", {"reference_type": "AMBIGUOUS", "candidate_product_ids": ["SKU022", "SKU026"]}, 3)
    assert result["status"] == "AMBIGUOUS"
    assert state.known_facts["selected_products"][0]["quantity"] == 1
