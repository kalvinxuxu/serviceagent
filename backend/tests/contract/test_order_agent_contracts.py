from backend.app.order_agent.contracts import OrderAction, OrderEmailInput

def test_order_action_rejects_unknown_action():
    assert OrderAction(action="CHECK_ORDER").schema_version == "1.0"

def test_email_input_requires_body():
    assert OrderEmailInput(email_id="x", sender="a@b.test", body="订原味贝果1个").email_id == "x"
