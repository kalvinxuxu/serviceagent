from backend.app.agent.contracts import ResponseContext
from backend.app.agent.response_composer import compose


def test_quote_response_is_natural_and_does_not_dump_policy_fields():
    reply = compose(ResponseContext(
        user_text="多少钱",
        action="REQUOTE",
        business_result={"items": [{"name": "原味贝果", "quantity": 2, "subtotal": 20}], "total": 20, "discount": 0, "delivery_mode": "PICKUP"},
    ))
    assert "合计 20 元" in reply
    assert "quote_context" not in reply
    assert "查询时间" not in reply
    assert "其他口味" in reply
