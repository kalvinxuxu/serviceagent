from backend.app.order_agent.email_parser import parse_email
def test_parser_extracts_multiple_items():
    result = parse_email("订单", "原味贝果2个，芝士贝果1个，明天送到公司", "a@test")
    assert result["classification"] == "ORDER" and len(result["items"]) == 2
def test_parser_marks_missing_items():
    assert "items" in parse_email("订单", "请尽快处理", "a@test")["missing_information"]
