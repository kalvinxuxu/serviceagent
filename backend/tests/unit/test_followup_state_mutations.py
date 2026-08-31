from backend.app.agent.state import CustomerServiceState
from evals.benchmark_assertions import bootstrap_fixture
from backend.app.agent.planner import plan


def test_browse_results_can_resolve_ranked_followup():
    bootstrap_fixture()
    state = CustomerServiceState(session_id="followup-rank", customer_id="CUS001")
    state.recommendation_candidates = ["SKU009", "SKU040"]
    state.known_facts["recommendations"] = [{"id": "SKU009", "product_id": "SKU009", "name": "\u829d\u58eb\u8d1d\u679c", "price": 13}, {"id": "SKU040", "product_id": "SKU040", "name": "\u53cc\u91cd\u5de7\u514b\u529b\u8d1d\u679c", "price": 6}]
    state.known_facts["understanding"] = {"goals": ["PRICE_CALCULATION"]}
    second = plan(state, "\u90a3\u6700\u4fbf\u5b9c\u7684\u6765\u4e24\u4e2a\u3002")
    assert second.next_action.tool_name == "calculate_order_quote"
    assert second.next_action.arguments["items"][0]["quantity"] == 2


def test_category_quantity_mutation_updates_selected_items_without_accumulating():
    bootstrap_fixture()
    state = CustomerServiceState(session_id="followup-category", customer_id="CUS001")
    state.known_facts["selected_products"] = [{"product_id": "SKU022", "name": "\u539f\u5473\u8d1d\u679c", "quantity": 2, "unit_price": 10}, {"product_id": "SKU026", "name": "\u751f\u5410\u53f8", "quantity": 1, "unit_price": 14}]
    state.known_facts["resolved_products"] = [{"query": "\u8d1d\u679c", "quantity": 3, "operation": "SET_QUANTITY"}]
    state.known_facts["understanding"] = {"goals": ["PRICE_CALCULATION"]}
    trace = plan(state, "\u8d1d\u679c\u6539\u6210\u4e09\u4e2a\u3002")
    assert trace.next_action.tool_name == "calculate_order_quote"
    items = trace.next_action.arguments["items"]
    assert next(item["quantity"] for item in items if item["name"] == "\u539f\u5473\u8d1d\u679c") == 3
    assert next(item["quantity"] for item in items if item["name"] == "\u751f\u5410\u53f8") == 1


def test_keep_quantity_preserves_existing_working_set():
    bootstrap_fixture()
    state = CustomerServiceState(session_id="followup-keep", customer_id="CUS001")
    state.known_facts["selected_products"] = [
        {"product_id": "SKU022", "name": "原味贝果", "quantity": 3, "unit_price": 10},
        {"product_id": "SKU026", "name": "生吐司", "quantity": 1, "unit_price": 14},
    ]
    state.quote_context = type("Quote", (), {"items": state.known_facts["selected_products"]})()
    state.known_facts["understanding"] = {"goals": ["PRICE_CALCULATION"]}
    result = plan(state, "吐司还是一个。")
    assert result.reason_code == "SELECTION_CONFIRMED_UNCHANGED"
    assert [(item["name"], item["quantity"]) for item in result.next_action.arguments["items"]] == [("原味贝果", 3), ("生吐司", 1)]
