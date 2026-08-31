import pytest
from backend.app.agent.contracts import PlannerOutput

def test_planner_output_is_structured_and_forbids_unknown_fields():
    output = PlannerOutput.model_validate({"goal":{"type":"INVENTORY_CHECK"},"next_action":{"type":"TOOL_CALL","tool_name":"check_inventory","arguments":{"product_id":"SKU001"}},"reason_code":"INVENTORY_REQUIRED"})
    assert output.next_action.type == "TOOL_CALL"
    with pytest.raises(Exception):
        PlannerOutput.model_validate({"goal":{"type":"X"},"next_action":{"type":"RESPOND","message":"ok"},"reason_code":"x","unsafe":"run"})
