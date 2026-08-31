import json
from pathlib import Path

from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed


SCENARIOS = Path(__file__).resolve().parents[3] / "evals" / "scenarios" / "customer_service_quality_v1.json"


def test_quality_suite_contains_twenty_scenarios():
    cases = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    assert len(cases) == 20
    assert {case["category"] for case in cases} == {"RECOMMENDATION", "STORE_SERVICE"}
    assert all(case["expected"]["required_capabilities"] for case in cases)


def test_recommendation_reply_is_customer_friendly(monkeypatch):
    load_products_from_seed()
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    state, reply, trace = run_turn(CustomerServiceState(session_id="quality-recommendation"), "给家里老人推荐一些早餐面包，不要太甜")
    assert trace["next_action"]["tool_name"] == "recommend_products"
    assert "元" in reply and len(reply) > 40
    assert "标签：" not in reply
    assert "可售" not in reply


def test_store_service_faq_uses_tool_and_natural_reply(monkeypatch):
    load_products_from_seed()
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    state, reply, trace = run_turn(CustomerServiceState(session_id="quality-faq"), "面包当天吃不完，应该怎么保存？")
    assert trace["next_action"]["tool_name"] == "answer_store_faq"
    assert "保存" in reply or "密封" in reply
