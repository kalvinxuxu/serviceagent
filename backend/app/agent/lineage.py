from __future__ import annotations

from typing import Final

CORE_COMPONENTS: Final[tuple[str, ...]] = (
    "SEMANTIC_UNDERSTANDING",
    "REFERENCE_RESOLVER",
    "SUPERVISOR_ROUTER",
    "GOAL_MANAGER",
    "CAPABILITY_POLICY",
    "ACTION_PLANNER",
    "POLICY_GATE",
    "EXECUTOR",
    "STATE_UPDATER",
    "RESPONSE_COMPOSER",
    "TURN_EVALUATOR",
)


def first_failure(steps: list[dict]) -> str | None:
    for step in steps:
        if step.get("status") == "FAIL":
            return step.get("component")
    return None


def mark_downstream_not_run(steps: list[dict], failure_component: str | None) -> list[dict]:
    if not failure_component:
        return steps
    failed = False
    for step in steps:
        if step.get("component") == failure_component:
            failed = True
            continue
        if failed and step.get("status") == "PASS":
            step["status"] = "NOT_RUN"
    return steps
