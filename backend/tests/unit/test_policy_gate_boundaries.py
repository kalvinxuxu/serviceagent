from backend.app.agent.policy_gate import decide


def test_read_only_action_is_allowed_without_confirmation():
    decision = decide("check_inventory")
    assert decision.decision == "ALLOW"
    assert decision.reason_code == "READ_ONLY"


def test_side_effect_requires_confirmation():
    decision = decide("create_return_request")
    assert decision.decision == "REQUIRE_CONFIRMATION"
    assert decision.requires_confirmation is False


def test_forbidden_side_effect_is_denied():
    assert decide("delete_customer_data").decision == "DENY"


def test_unknown_side_effect_escalates():
    assert decide("unknown_side_effect").decision == "ESCALATE"
