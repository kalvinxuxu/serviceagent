from backend.app.agent.reference_resolver import resolve_semantic_target
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed


load_products_from_seed()


def _state():
    state = CustomerServiceState(session_id="reference-actions")
    state.recommendation_candidates = ["SKU022", "SKU026"]
    state.reference_context = {
        "candidate_set": [
            {"product_id": "SKU022", "position": 1},
            {"product_id": "SKU026", "position": 2},
        ]
    }
    state.known_facts["recommendations"] = [
        {"id": "SKU022", "name": "原味贝果", "price": 10},
        {"id": "SKU026", "name": "生吐司", "price": 14},
    ]
    return state


def test_resolves_second_candidate():
    result = resolve_semantic_target(_state(), {"type": "REFERENCE", "value": "SECOND"})
    assert result["resolved_product_ids"] == ["SKU026"]


def test_resolves_cheapest_candidate():
    result = resolve_semantic_target(_state(), {"type": "REFERENCE", "value": "CHEAPEST"})
    assert result["resolved_product_ids"] == ["SKU022"]


def test_category_reference_resolves_selected_item_from_catalog():
    state = _state()
    state.known_facts["selected_products"] = [{"product_id": "SKU022", "quantity": 1}]
    result = resolve_semantic_target(state, {"type": "CATEGORY", "value": "贝果"})
    assert result["resolved_product_ids"] == ["SKU022"]
