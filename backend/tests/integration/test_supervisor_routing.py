from backend.app.agent.contracts import UnderstandingOutput
from backend.app.agent.supervisor import SupervisorAgent


def test_supervisor_routes_commerce_and_after_sales():
    agent = SupervisorAgent()
    commerce = agent.decide(UnderstandingOutput(goals=["PRICE_CALCULATION"], requested_items=[]), "商品多少钱")
    after_sales = agent.decide(UnderstandingOutput(goals=["RETURN"]), "我要退货")
    assert commerce.domain == "COMMERCE"
    assert commerce.tasks[0].target_agent == "COMMERCE"
    assert after_sales.tasks[0].target_agent == "AFTER_SALES"


def test_supervisor_supports_parallel_mixed_goals_and_handoff():
    agent = SupervisorAgent()
    mixed = agent.decide(UnderstandingOutput(goals=["PRICE_CALCULATION", "INVENTORY_CHECK"]), "多少钱还有货")
    human = agent.decide(UnderstandingOutput(goals=["OTHER"]), "请转人工")
    assert mixed.route_action == "PARALLEL_TASKS"
    assert {task.target_agent for task in mixed.tasks} == {"COMMERCE"}
    assert human.route_action == "HANDOFF"


def test_supervisor_asks_for_missing_goal_without_tool_capability():
    decision = SupervisorAgent().decide(UnderstandingOutput(), "")
    assert decision.route_action == "ASK_USER"
    assert decision.missing_information == ["goal"]
