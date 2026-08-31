from backend.app.tools.registry import execute
from backend.app.domain.return_service import create_return_request

def test_unsafe_tool_and_unconfirmed_side_effect_are_blocked():
    assert not execute("delete_customer", {}).ok
    assert create_return_request("ORD001", "CUS001", False)["reason"] == "CONFIRMATION_REQUIRED"
