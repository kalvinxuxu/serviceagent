from backend.app.agent.planner import plan
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed

load_products_from_seed()

def test_planner_returns_machine_actions():
    state=CustomerServiceState(session_id="s")
    assert plan(state, "你好").next_action.type == "ASK_USER"
    assert plan(state, "请转人工").next_action.type == "HANDOFF"

def test_planner_routes_new_product_inventory_query_to_inventory_tool():
    state = CustomerServiceState(session_id="planner-inventory")
    output = plan(state, "有原味贝果吗")
    assert output.next_action.type == "TOOL_CALL"
    assert output.next_action.tool_name == "check_inventory"
    assert output.next_action.arguments["product_id"] == "SKU022"

def test_planner_routes_generic_bread_availability_to_inventory_listing():
    state = CustomerServiceState(session_id="planner-recommendation")
    output = plan(state, "现在还有什么面包")
    assert output.next_action.type == "TOOL_CALL"
    assert output.next_action.tool_name == "list_available_inventory"


def test_planner_treats_bare_bread_category_as_browse_request():
    state = CustomerServiceState(session_id="planner-category-short-reply")
    output = plan(state, "欧包")
    assert output.next_action.type == "TOOL_CALL"
    assert output.next_action.tool_name == "list_available_inventory"
    assert output.next_action.arguments["category"] == "欧包"


def test_planner_offers_human_after_three_unresolved_turns_without_auto_handoff():
    state = CustomerServiceState(session_id="handoff-offer")
    state.turn_count = 3
    output = plan(state, "还是没解决")
    assert output.next_action.type == "ASK_USER"
    assert output.reason_code == "CLARIFICATION_ESCALATION_OFFER"
    assert state.known_facts["handoff_offer"] is True


def test_planner_consumes_category_from_terse_followup_understanding():
    from backend.app.agent.understanding import understand
    state = CustomerServiceState(session_id="planner-category-followup")
    semantic = understand(state, "那吐司呢？")
    state.known_facts["understanding"] = semantic.model_dump()
    state.known_facts["understanding_status"] = "VALID"
    output = plan(state, "那吐司呢？")
    assert output.next_action.tool_name == "list_available_inventory"
    assert output.next_action.arguments["category"] == "吐司"

def test_planner_does_not_handoff_after_product_queries():
    state = CustomerServiceState(session_id="planner-sequence")
    plan(state, "现在还有什么面包")
    plan(state, "有原味贝果吗")
    output = plan(state, "有生吐司吗")
    assert output.next_action.tool_name == "check_inventory"
    assert output.next_action.arguments["product_id"] == "SKU026"

def test_planner_calculates_total_from_confirmed_products():
    state = CustomerServiceState(session_id="planner-total")
    state.known_facts["selected_products"] = [{"product_id": "SKU022", "quantity": 1}]
    output = plan(state, "一起要多少钱")
    assert output.next_action.tool_name == "calculate_order_quote"
    assert output.next_action.arguments["items"][0]["product_id"] == "SKU022"

def test_planner_extracts_quantity_from_explicit_price_request():
    state = CustomerServiceState(session_id="planner-explicit-quantity")
    output = plan(state, "要2个芝士贝果，多少钱")
    assert output.next_action.tool_name == "calculate_order_quote"
    assert output.next_action.arguments["items"][0]["product_id"] == "SKU009"
    assert output.next_action.arguments["items"][0]["quantity"] == 2


def test_planner_promotes_focused_inventory_product_on_quantity_purchase():
    state = CustomerServiceState(session_id="focused-quantity")
    state.focused_product = {"product_id": "SKU026", "name": "生吐司", "quantity": 1, "unit_price": 14}
    output = plan(state, "要2个，多收钱")
    assert output.next_action.tool_name == "calculate_order_quote"
    assert output.next_action.arguments["items"][0]["quantity"] == 2
    assert state.known_facts["selected_products"][0]["product_id"] == "SKU026"


def test_planner_asks_when_quantity_reference_has_multiple_recent_products():
    state = CustomerServiceState(session_id="ambiguous-quantity")
    state.recent_products = [{"product_id": "SKU022", "name": "原味贝果"}, {"product_id": "SKU026", "name": "生吐司"}]
    output = plan(state, "要两个")
    assert output.reason_code == "AMBIGUOUS_REFERENCE"
    assert output.next_action.type == "ASK_USER"

def test_goal_transition_switches_inventory_to_price_calculation():
    from backend.app.agent.goal_stack import transition_goals
    state = CustomerServiceState(session_id="goal-switch")
    state.goals = [{"id": "g1", "type": "INVENTORY_CHECK", "status": "ACTIVE", "priority": 1}]
    transitions = transition_goals(state, ["PRICE_CALCULATION"])
    assert state.goals[0]["status"] == "COMPLETED"
    assert any(item["transition"] == "CREATE" and item["detected_goal"] == "PRICE_CALCULATION" for item in transitions)


def test_multi_item_request_routes_to_quote_without_inventory_listing():
    from backend.app.agent.understanding import resolve_products, understand
    state = CustomerServiceState(session_id="multi-item-quote")
    semantic = understand(state, "要两个低糖欧包，一个红豆面包")
    state.known_facts["understanding"] = semantic.model_dump()
    state.known_facts["resolved_products"] = resolve_products(semantic)
    output = plan(state, "要两个低糖欧包，一个红豆面包")
    assert output.next_action.tool_name == "calculate_order_quote"
    assert [(item["product_id"], item["quantity"]) for item in output.next_action.arguments["items"]] == [("SKU006", 2), ("SKU015", 1)]


def test_invalid_llm_output_fails_safely_without_listing_inventory():
    state = CustomerServiceState(session_id="invalid-understanding")
    state.known_facts["understanding_status"] = "FAILED"
    state.known_facts["resolved_products"] = [{"query": "未知面包", "candidates": [{"product_id": "SKU006", "name": "低糖欧包", "category": "早餐"}]}]
    output = plan(state, "未知面包多少钱")
    assert output.reason_code == "LLM_OUTPUT_INVALID"
    assert output.next_action.type == "ASK_USER"
    assert output.next_action.tool_name is None


def test_operation_sequence_updates_quote_items():
    from backend.app.agent.understanding import resolve_products, understand
    state = CustomerServiceState(session_id="operation-sequence")
    first = understand(state, "要两个低糖欧包，一个红豆面包")
    state.known_facts["understanding"] = first.model_dump()
    state.known_facts["resolved_products"] = resolve_products(first)
    plan(state, "要两个低糖欧包，一个红豆面包")
    state.known_facts["selected_products"] = [
        {"product_id": "SKU006", "name": "低糖欧包", "quantity": 2},
        {"product_id": "SKU015", "name": "红豆面包", "quantity": 1},
    ]
    removed = understand(state, "红豆面包不要了")
    state.known_facts["understanding"] = removed.model_dump()
    state.known_facts["resolved_products"] = resolve_products(removed)
    assert plan(state, "红豆面包不要了").next_action.tool_name == "edit_selected_items"
    changed = understand(state, "低糖欧包改成三个")
    state.known_facts["understanding"] = changed.model_dump()
    state.known_facts["resolved_products"] = resolve_products(changed)
    output = plan(state, "低糖欧包改成三个")
    assert output.next_action.tool_name == "edit_selected_items"
    assert output.next_action.arguments["items"][0]["quantity"] == 3


def test_keep_reference_does_not_switch_inventory_query_back_to_pricing():
    from backend.app.agent.understanding import resolve_products, understand
    state = CustomerServiceState(session_id="keep-reference")
    state.known_facts["selected_products"] = [{"product_id": "SKU006", "name": "低糖欧包", "quantity": 2}]
    semantic = understand(state, "那有什么吐司吗？")
    state.known_facts["understanding"] = semantic.model_dump()
    state.known_facts["resolved_products"] = resolve_products(semantic)
    output = plan(state, "那有什么吐司吗？")
    assert output.goal.type == "PRODUCT_BROWSE"
    assert output.next_action.tool_name == "list_available_inventory"
