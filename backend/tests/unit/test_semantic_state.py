from backend.app.agent.semantic_state import apply_constraint_updates, merge_understanding_state, normalize_semantic_state
from backend.app.agent.feedback import detect_feedback


def test_normalize_semantic_state_accepts_flat_and_5w_shapes():
    state = normalize_semantic_state({"audience": "SENIOR", "how": {"texture": "SOFT"}})
    assert state["who"]["audience"] == "SENIOR"
    assert state["how"]["texture"] == "SOFT"


def test_constraint_updates_can_remove_sticky_constraint():
    state = apply_constraint_updates({"who": {"audience": "CHILD"}, "how": {"sweetness": "LOW"}}, {"set": {"audience": "SENIOR"}, "remove": ["sweetness"]})
    assert state["who"]["audience"] == "SENIOR"
    assert "sweetness" not in state["how"]


def test_current_semantic_facts_overwrite_previous_facts():
    state = merge_understanding_state({"who": {"audience": "CHILD"}}, {"who": {"audience": "SENIOR"}, "when": {"needed_at": "tomorrow_morning"}}, {})
    assert state["who"]["audience"] == "SENIOR"
    assert state["when"]["needed_at"] == "tomorrow_morning"


def test_feedback_detects_explicit_goal_correction():
    event = detect_feedback("不是，我问的是价格", {"goals": ["INVENTORY_CHECK"]})
    assert event["target_component"] == "UNDERSTANDING"
    assert event["corrected_value"] == "PRICE_CALCULATION"
