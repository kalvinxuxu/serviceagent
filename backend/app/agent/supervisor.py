import asyncio
import json
import os
import threading

from .contracts import UnderstandingOutput
from .multi_agent_contracts import SupervisorDecision
from .prompts.supervisor import SUPERVISOR_SYSTEM_PROMPT
from .supervisor_router import build_tasks, route_action
from .state import Message
from ..llm import get_provider


def _run(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    result = []
    thread = threading.Thread(target=lambda: result.append(asyncio.run(coro)))
    thread.start()
    thread.join()
    return result[0]


class SupervisorAgent:
    """Route work only; domain calculations remain in domain agents/services."""

    def decide(self, understanding: UnderstandingOutput, user_text: str) -> SupervisorDecision:
        if os.getenv("LLM_PROVIDER", "mock").lower() in {"deepseek", "openai"}:
            try:
                decision = _run(get_provider().structured_generate(
                    messages=[
                        Message(role="system", content=SUPERVISOR_SYSTEM_PROMPT),
                        Message(
                            role="user",
                            content=json.dumps(
                                {
                                    "user_message": user_text,
                                    "understanding": understanding.model_dump(),
                                },
                                ensure_ascii=False,
                            ),
                        ),
                    ],
                    output_schema=SupervisorDecision,
                    temperature=0,
                ))
                return decision
            except Exception:
                # Routing must remain available when the provider is unavailable
                # or returns an invalid decision; the deterministic path still
                # validates the same SupervisorDecision contract.
                pass
        goals = understanding.goals or understanding.candidate_goals
        action = route_action(goals, user_text)
        tasks = build_tasks(goals)
        if action == "HANDOFF":
            return SupervisorDecision(
                goals=goals or ["OTHER"], domain="HUMAN", route_action=action,
                reason_code="CUSTOMER_REQUESTED_HUMAN", confidence=1.0,
            )
        if action == "ASK_USER":
            return SupervisorDecision(
                goals=goals or ["OTHER"], domain="UNKNOWN", route_action=action,
                reason_code="GOAL_MISSING", confidence=0.2, missing_information=["goal"],
            )
        domain = "AFTER_SALES" if tasks[0].target_agent == "AFTER_SALES" and len(tasks) == 1 else "COMMERCE"
        return SupervisorDecision(
            goals=goals, domain=domain, route_action=action, tasks=tasks,
            reason_code="MULTI_GOAL_ROUTE" if len(tasks) > 1 else "DOMAIN_ROUTE",
            confidence=0.9,
        )
