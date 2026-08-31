import pytest
from backend.app.agent.contracts import NextAction
from backend.app.tools.contracts import ToolRequest

def test_component_contracts_reject_invalid_actions():
    with pytest.raises(Exception):
        NextAction(type="TOOL_CALL")
    assert ToolRequest(tool_name="check_inventory").arguments == {}
