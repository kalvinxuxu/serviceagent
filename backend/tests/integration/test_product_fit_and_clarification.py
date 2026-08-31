from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed, seed_inventory


def test_fit_question_uses_fit_tool_not_inventory():
    load_products_from_seed()
    seed_inventory()
    state = CustomerServiceState(session_id="fit_query_test")
    state, reply, trace = run_turn(state, "生吐司适合小朋友吃吗")
    assert trace["goal"]["type"] == "PRODUCT_FIT_QUERY"
    assert trace["next_action"]["tool_name"] == "explain_product_fit"
    assert "库存" not in reply


def test_ambiguous_question_asks_for_clarification():
    state = CustomerServiceState(session_id="ambiguous_query_test")
    state, reply, trace = run_turn(state, "有什么什么时候老人家吃的？")
    assert trace["next_action"]["type"] == "ASK_USER"
    assert state.status == "WAITING_USER"
    assert "适合老人" in reply or "什么时候" in reply


def test_category_cheapest_uses_compare_without_handoff():
    load_products_from_seed()
    state = CustomerServiceState(session_id="category_compare_test")
    state, reply, trace = run_turn(state, "\u76d0\u9762\u5305\u91cc\u9762\u6700\u4fbf\u5b9c\u7684\u662f\u54ea\u4e2a\uff1f")
    assert trace["goal"]["type"] == "PRODUCT_COMPARE"
    assert trace["next_action"]["tool_name"] == "compare_products"
    assert state.status != "HANDOFF"
    assert reply
