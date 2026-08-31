from backend.app.agent.understanding import normalize_message, extract_known_facts
from backend.app.agent.evaluator import should_handoff

def test_understanding_component_is_independent():
    assert normalize_message("  你好   我想退货 ") == "你好 我想退货"
    assert extract_known_facts("昨天买的低糖面包") == {"purchase_time":"昨天", "preference":"低糖"}

def test_evaluator_component_has_safe_handoff_boundary():
    assert should_handoff(3, "INTENT_UNCLEAR")
    assert should_handoff(1, "HUMAN_REQUEST_OR_HIGH_RISK")
