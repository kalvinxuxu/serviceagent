from backend.app.agent.policy_gate import decide


def test_policy_gate_decisions():
    assert decide("check_inventory").decision == "ALLOW"
    assert decide("delete_customer_data").decision == "DENY"
    assert decide("create_return_request").decision == "REQUIRE_CONFIRMATION"
    assert decide("create_return_request", confirmed=True).decision == "ALLOW"
