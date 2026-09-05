from backend.app.agent.contracts import UnderstandingOutput
from backend.app.agent.supervisor import SupervisorAgent


def test_domain_router_is_independent_from_legacy_task_routing():
    decision = SupervisorAgent().decide_domain(UnderstandingOutput(goals=["RETURN"]), "我要退货")
    assert decision.domain == "AFTER_SALES"
    assert set(decision.model_dump()) == {"domain", "confidence", "reason_code"}


def test_human_request_does_not_become_human_domain():
    decision = SupervisorAgent().decide_domain(UnderstandingOutput(goals=["RETURN"]), "我要转人工")
    assert decision.domain == "UNKNOWN"
    assert decision.reason_code == "HUMAN_HANDOFF"
