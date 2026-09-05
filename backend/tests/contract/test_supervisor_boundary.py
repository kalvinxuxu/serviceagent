from backend.app.agent.commerce_capabilities import COMMERCE_CAPABILITIES
from backend.app.agent.supervisor import SupervisorAgent
from backend.app.agent.contracts import UnderstandingOutput
from backend.app.agent.multi_agent_contracts import SupervisorDecision
from backend.app.agent.contracts import DomainRouteDecision


def test_supervisor_only_emits_route_tasks_not_business_tools():
    decision = SupervisorAgent().decide(UnderstandingOutput(goals=["INVENTORY_CHECK"]), "有货吗")
    assert all(task.target_agent in {"COMMERCE", "AFTER_SALES", "HUMAN"} for task in decision.tasks)
    assert "calculate_order_quote" in COMMERCE_CAPABILITIES
    assert decision.model_dump().get("tool_name") is None


def test_supervisor_uses_structured_provider_for_deepseek(monkeypatch):
    calls = []

    class StubProvider:
        async def structured_generate(self, *, messages, output_schema, temperature=0):
            calls.append((messages, output_schema, temperature))
            return SupervisorDecision(
                goals=["PRICE_CALCULATION"],
                domain="COMMERCE",
                route_action="CONTINUE_AGENT",
                tasks=[{"id": "commerce-price", "target_agent": "COMMERCE"}],
                reason_code="LLM_ROUTE",
                confidence=0.94,
            )

    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setattr("backend.app.agent.supervisor.get_provider", lambda: StubProvider())

    decision = SupervisorAgent().decide(
        UnderstandingOutput(goals=["PRICE_CALCULATION"]),
        "两个吐司多少钱？",
    )

    assert decision.reason_code == "LLM_ROUTE"
    assert calls and calls[0][1] is SupervisorDecision


def test_supervisor_falls_back_safely_when_provider_fails(monkeypatch):
    class BrokenProvider:
        async def structured_generate(self, **kwargs):
            raise RuntimeError("provider unavailable")

    monkeypatch.setenv("LLM_PROVIDER", "deepseek")
    monkeypatch.setattr("backend.app.agent.supervisor.get_provider", lambda: BrokenProvider())

    decision = SupervisorAgent().decide(
        UnderstandingOutput(goals=["INVENTORY_CHECK"]),
        "还有货吗？",
    )

    assert decision.domain == "COMMERCE"
    assert decision.tasks
    assert decision.reason_code == "DOMAIN_ROUTE"


def test_converged_supervisor_domain_route_cannot_emit_human_or_actions():
    decision = SupervisorAgent().decide_domain(UnderstandingOutput(goals=["INVENTORY_CHECK"]), "有货吗")
    assert isinstance(decision, DomainRouteDecision)
    assert decision.domain == "COMMERCE"
    assert set(decision.model_dump()) == {"domain", "confidence", "reason_code"}


def test_converged_human_request_is_unknown_domain_with_handoff_reason():
    decision = SupervisorAgent().decide_domain(UnderstandingOutput(goals=[]), "请转人工客服")
    assert decision.domain == "UNKNOWN"
    assert decision.reason_code == "HUMAN_HANDOFF"
