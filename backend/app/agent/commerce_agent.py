from typing import Any

from .commerce_capabilities import COMMERCE_CAPABILITIES
from .contracts import PlannerOutput
from .multi_agent_contracts import AgentTask
from .planner import plan
from .state import CustomerServiceState
from ..domain.preference_service import normalize
from ..domain.recommendation_service import recommend


class CommerceAgent:
    """Stable Commerce boundary around the existing planner and domain services."""

    def capabilities(self) -> list[str]:
        return list(COMMERCE_CAPABILITIES)

    def intake(self, task: AgentTask, state: CustomerServiceState) -> dict[str, Any]:
        if task.target_agent != "COMMERCE":
            return {"ok": False, "reason_code": "WRONG_AGENT", "capabilities": []}
        return {
            "ok": True,
            "task_id": task.id,
            "capabilities": self.capabilities(),
            "quote_context": state.quote_context.model_dump() if state.quote_context else None,
        }

    def plan_turn(self, state: CustomerServiceState, text: str, capabilities: list[str]) -> PlannerOutput:
        allowed = set(capabilities).intersection(COMMERCE_CAPABILITIES)
        return plan(state, text, sorted(allowed))

    def recommend(self, preference_text: str) -> list[dict[str, Any]]:
        constraints = normalize(preference_text)
        return recommend(**constraints)
