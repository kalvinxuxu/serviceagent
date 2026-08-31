import asyncio

from backend.app.agent.contracts import PlannerDecision
from backend.app.agent.state import Message
from backend.app.llm.mock import MockProvider


def test_mock_provider_returns_valid_structured_planner_decision():
    decision = asyncio.run(MockProvider().structured_generate(
        messages=[Message(role="user", content="我有个问题想咨询")],
        output_schema=PlannerDecision,
    ))
    assert decision.action_type == "ASK_USER"
    assert decision.reason_code == "INTENT_UNCLEAR"
