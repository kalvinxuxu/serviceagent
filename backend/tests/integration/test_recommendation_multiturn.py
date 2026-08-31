from backend.app.agent import understanding, supervisor
from backend.app.agent.contracts import UnderstandingOutput
from backend.app.agent.graph import run_turn
from backend.app.agent.multi_agent_contracts import SupervisorDecision
from backend.app.agent.state import CustomerServiceState
from backend.app.db.seed import load_products_from_seed
from backend.app.domain.recommendation_service import normalize_constraints


class RecommendationUnderstandingStub:
    def __init__(self):
        self.calls = 0

    async def structured_generate(self, *, messages, output_schema, temperature=0):
        if output_schema is UnderstandingOutput:
            self.calls += 1
            constraints = {"audience": ["儿童"]} if self.calls == 1 else {"texture": ["柔软"]}
            return UnderstandingOutput(goals=["PRODUCT_RECOMMENDATION"], constraints=constraints)
        if output_schema is SupervisorDecision:
            return SupervisorDecision(
                goals=["PRODUCT_RECOMMENDATION"], domain="COMMERCE", route_action="CONTINUE_AGENT",
                tasks=[{"id": "commerce-recommendation", "target_agent": "COMMERCE"}],
                reason_code="STUB_ROUTE", confidence=1.0,
            )
        raise AssertionError(f"unexpected schema: {output_schema}")


def test_recommendation_follow_up_updates_structured_constraint(monkeypatch):
    load_products_from_seed()
    stub = RecommendationUnderstandingStub()
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setattr(understanding, "get_provider", lambda: stub)
    monkeypatch.setattr(supervisor, "get_provider", lambda: stub)
    state = CustomerServiceState(session_id="recommendation-follow-up")

    state, first_reply, first_trace = run_turn(state, "有什么适合小朋友吃的面包吗")
    first_ids = [item["id"] for item in state.known_facts["recommendations"]]
    state, second_reply, second_trace = run_turn(state, "软一点的")
    context = state.known_facts["recommendation_context"]
    second_ids = [item["id"] for item in state.known_facts["recommendations"]]

    assert first_trace["next_action"]["tool_name"] == "recommend_products"
    assert second_trace["next_action"]["tool_name"] == "recommend_products"
    assert context["constraints"]["audience"] == ["儿童"]
    assert context["constraints"]["texture"] == ["柔软"]
    assert first_ids != second_ids
    assert "明白" in second_reply
    assert "可售" not in second_reply and "标签：" not in second_reply


def test_recommendation_context_is_preserved_for_refresh(monkeypatch):
    load_products_from_seed()
    stub = RecommendationUnderstandingStub()
    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setattr(understanding, "get_provider", lambda: stub)
    monkeypatch.setattr(supervisor, "get_provider", lambda: stub)
    state = CustomerServiceState(session_id="recommendation-refresh")
    state, _, _ = run_turn(state, "有什么适合小朋友吃的面包吗")
    previous_ids = set(item["id"] for item in state.known_facts["recommendations"])
    state, _, trace = run_turn(state, "软一点的")
    current_ids = set(item["id"] for item in state.known_facts["recommendations"])
    assert trace["next_action"]["arguments"]["constraints"]["audience"] == ["儿童"]
    assert not current_ids.intersection(previous_ids)


def test_recommendation_constraint_normalization_accepts_llm_scalar_values():
    normalized = normalize_constraints({"audience": "小朋友", "texture": "软"})
    assert normalized["audience"] == ["儿童"]
    assert normalized["texture"] == ["柔软"]
