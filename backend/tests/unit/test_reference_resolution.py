from backend.app.agent.reference_resolver import resolve_reference
from backend.app.agent.state import CustomerServiceState


def test_inventory_focus_is_not_purchase_selection():
    state = CustomerServiceState(session_id="reference-focus")
    state.focused_product = {"product_id": "SKU026", "name": "生吐司"}
    assert resolve_reference(state)["reference_type"] == "FOCUSED_PRODUCT"
    assert state.known_facts.get("selected_products", []) == []


def test_multiple_recommendation_candidates_are_ambiguous():
    state = CustomerServiceState(session_id="reference-ambiguous")
    state.recommendation_candidates = ["SKU022", "SKU026"]
    result = resolve_reference(state)
    assert result["reference_type"] == "AMBIGUOUS"
    assert result["resolved_product_ids"] == []


def test_rank_reference_resolves_candidate_ids_from_catalog():
    state = CustomerServiceState(session_id="reference-rank")
    state.recommendation_candidates = ["SKU001", "SKU026"]
    result = resolve_reference(state, text="第一个多少钱")
    assert result["reference_type"] == "RECOMMENDATION_RANK"
    assert result["resolved_product_ids"] == ["SKU001"]


def test_reference_context_is_preferred_for_ordinal_resolution():
    state = CustomerServiceState(session_id="reference-context")
    state.reference_context = {
        "candidate_set": [
            {"product_id": "SKU026", "position": 1, "source": "PRODUCT_BROWSE"},
            {"product_id": "SKU001", "position": 2, "source": "PRODUCT_BROWSE"},
        ]
    }
    result = resolve_reference(state, text="第一个多少钱")
    assert result["resolved_product_ids"] == ["SKU026"]
