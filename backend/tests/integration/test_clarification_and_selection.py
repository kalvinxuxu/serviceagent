import pytest

from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed, seed_inventory


def test_recommendation_selection_asks_quantity_then_quotes(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    load_products_from_seed()
    seed_inventory()
    state = CustomerServiceState(session_id="selection-clarification")
    state, _, first_trace = run_turn(state, "\u6709\u4ec0\u4e48\u9002\u5408\u5c0f\u670b\u53cb\u5403\u7684\u9762\u5305\u5417")
    state, reply, second_trace = run_turn(state, "\u90a3\u8981\u65e5\u5f0f\u6930\u84c9\u8513\u8d8a\u8393")
    assert first_trace["next_action"]["tool_name"] == "recommend_products"
    assert second_trace["reason_code"] == "SELECTION_QUANTITY_REQUIRED"
    assert state.status == "WAITING_SELECTION"
    assert "几个" in reply
    assert state.known_facts["pending_selection"]["reference_source"] == "previous_recommendation_candidates"

    state, reply, third_trace = run_turn(state, "两个")
    assert third_trace["next_action"]["tool_name"] == "calculate_order_quote"
    assert state.quote_context and state.quote_context.total == 16
    assert state.status == "IN_PROGRESS"
    assert "\u65e5\u5f0f\u6930\u84c9\u8513\u8d8a\u8393×2" in reply


def test_inventory_lookup_promotes_focus_then_quantity_selects_and_quotes(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    load_products_from_seed()
    seed_inventory()
    state = CustomerServiceState(session_id="focus-to-selection")
    state, _, inventory_trace = run_turn(state, "有生吐司吗")
    assert inventory_trace["next_action"]["tool_name"] == "check_inventory"
    assert state.focused_product["product_id"] == "SKU026"
    assert state.known_facts.get("selected_products", []) == []
    state, reply, quote_trace = run_turn(state, "要2个，多收钱")
    assert quote_trace["next_action"]["tool_name"] == "calculate_order_quote"
    assert quote_trace["next_action"]["arguments"]["items"][0]["quantity"] == 2
    assert state.quote_context and state.quote_context.items[0]["quantity"] == 2
    assert "28" in reply


def test_delivery_request_starts_with_address_slot(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    state = CustomerServiceState(session_id="delivery-clarification")
    state, reply, trace = run_turn(state, "能邮寄吗")
    assert trace["reason_code"] == "DELIVERY_SLOT_REQUIRED"
    assert trace["goal"]["type"] == "SHIPPING_POLICY"
    assert state.status == "WAITING_USER"
    assert state.missing_slots[0]["name"] == "delivery_address"
    assert "地址" in reply
    assert "支持" in reply or "可以" in reply


def test_delivery_address_is_saved_and_next_slot_is_requested(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    state = CustomerServiceState(session_id="delivery-address-followup")
    state, _, first_trace = run_turn(state, "可以邮寄吗")
    assert first_trace["reason_code"] == "DELIVERY_SLOT_REQUIRED"
    address = "广东省，清远市，佛冈县，明珠花园401"
    state, reply, trace = run_turn(state, address)
    assert state.delivery_slots["delivery_address"] == address
    assert trace["reason_code"] == "DELIVERY_SLOT_REQUIRED"
    assert state.missing_slots[0]["name"] == "recipient_name"
    assert "收货人姓名" in reply
    assert trace["evaluation"]["component_scores"]["STATE_MANAGER"] == "PASS"


def test_repeated_delivery_prompt_is_not_reported_as_all_pass(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    state = CustomerServiceState(session_id="delivery-unchanged")
    state, _, _ = run_turn(state, "可以邮寄吗")
    state, _, _ = run_turn(state, "广东省，清远市，佛冈县，明珠花园401")
    state, _, trace = run_turn(state, "不是告诉你了吗")
    assert trace["reason_code"] == "DELIVERY_SLOT_REQUIRED"
    assert trace["evaluation"]["component_scores"]["STATE_MANAGER"] == "FAIL"
    assert trace["evaluation"]["failure_component"] == "STATE_MANAGER"


def test_pickup_default_and_delivery_mode_change_recalculates_quote(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    load_products_from_seed()
    seed_inventory()
    state = CustomerServiceState(session_id="pickup-quote")
    state, _, _ = run_turn(state, "有什么适合小朋友吃的面包吗")
    state, _, _ = run_turn(state, "那要日式椰蓉蔓越莓")
    state, reply, trace = run_turn(state, "1个")
    assert trace["next_action"]["tool_name"] == "calculate_order_quote"
    assert state.quote_context.shipping == 0
    assert "到店自取" in reply

    state, reply, trace = run_turn(state, "不需要邮购，到店取")
    assert trace["reason_code"] == "DELIVERY_MODE_UPDATED"
    assert trace["next_action"]["arguments"]["delivery_mode"] == "PICKUP"
    assert state.quote_context.shipping == 0
    assert "到店自取" in reply
    assert "当前运费 6" not in reply


def test_broad_bread_browse_uses_natural_category_summary(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    load_products_from_seed()
    seed_inventory()
    state, reply, trace = run_turn(CustomerServiceState(session_id="broad-browse"), "你好，有什么面包卖")
    assert trace["next_action"]["tool_name"] == "list_available_inventory"
    assert "可售" not in reply
    assert "您更想看哪一类" in reply


@pytest.mark.parametrize("architecture", ["legacy", "semantic"])
def test_displayed_multi_product_prices_are_quoted_in_both_architectures(monkeypatch, architecture):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("AGENT_ARCHITECTURE", architecture)
    load_products_from_seed()
    seed_inventory()
    state = CustomerServiceState(session_id=f"displayed-multi-price-{architecture}")
    state, _, _ = run_turn(state, "现在有什么面包？")
    state, _, _ = run_turn(state, "有什么吐司吗？")
    state, reply, trace = run_turn(state, "原味吐司（14元），蔓越莓吐司（17元）各要1个，多少钱？")

    assert trace["next_action"]["tool_name"] == "calculate_order_quote"
    items = trace["next_action"]["arguments"]["items"]
    assert {(item["name"], item["quantity"]) for item in items} == {("原味吐司", 1), ("蔓越莓吐司", 1)}
    assert state.quote_context and state.quote_context.total == 28
    assert "28" in reply
