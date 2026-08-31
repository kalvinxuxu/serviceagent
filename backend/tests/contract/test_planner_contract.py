from backend.app.agent.contracts import PlannerOutput

def test_planner_contract_contains_next_action_and_reason():
    result=PlannerOutput.model_validate({"goal":{"type":"X"},"next_action":{"type":"ASK_USER","message":"补充信息"},"reason_code":"MISSING"})
    assert result.reason_code == "MISSING"
