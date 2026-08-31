from backend.app.agent import planner, understanding, supervisor
from backend.app.agent.contracts import PlannerDecision, UnderstandingOutput
from backend.app.agent.multi_agent_contracts import SupervisorDecision
from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState


class StubLLM:
    async def structured_generate(self, *, messages, output_schema, temperature=0):
        if output_schema is UnderstandingOutput:
            return UnderstandingOutput.model_validate({
                "candidate_goals": ["INVENTORY_CHECK"],
                "product_mentions": [{"text": "原味的贝果", "product_query": "原味贝果"}],
                "references": [],
            })
        if output_schema is SupervisorDecision:
            return SupervisorDecision.model_validate({
                "goals": ["INVENTORY_CHECK"],
                "domain": "COMMERCE",
                "route_action": "CONTINUE_AGENT",
                "tasks": [{"id": "commerce-inventory", "target_agent": "COMMERCE"}],
                "reason_code": "STUB_ROUTE",
                "confidence": 1.0,
            })
        return PlannerDecision.model_validate({
            "goal_type": "INVENTORY_CHECK",
            "current_goal_id": "goal_inventory",
            "action_type": "TOOL_CALL",
            "tool_name": "check_inventory",
            "tool_args": {"product_id": "SKU022"},
            "reason_code": "PRODUCT_RESOLVED_FROM_SEMANTIC_CONTEXT",
            "expected_state_transition": "IN_PROGRESS",
        })


def test_llm_understanding_and_planner_select_inventory_tool(monkeypatch):
    stub = StubLLM()
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setattr(understanding, "get_provider", lambda: stub)
    monkeypatch.setattr(planner, "get_provider", lambda: stub)
    monkeypatch.setattr(supervisor, "get_provider", lambda: stub)

    state = CustomerServiceState(session_id="llm-pipeline", customer_id="CUS001")
    state, reply, trace = run_turn(state, "原味的贝果现在还能买吗")

    assert trace["next_action"]["tool_name"] == "check_inventory"
    assert trace["next_action"]["arguments"] == {"product_id": "SKU022"}
    assert "可售库存" in reply
