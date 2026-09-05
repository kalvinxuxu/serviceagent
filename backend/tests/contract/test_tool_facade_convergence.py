from backend.app.tools.registry import canonical_tool_name


def test_delivery_tool_aliases_share_one_canonical_operation():
    assert canonical_tool_name("submit_delivery_request") == "create_delivery_request"
    assert canonical_tool_name("create_order") == "create_delivery_request"


def test_canonical_tool_name_preserves_distinct_operations():
    assert canonical_tool_name("check_inventory") == "check_inventory"
