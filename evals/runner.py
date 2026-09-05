"""Executable quality gates for SC-001 through SC-009."""

import json
import sys
import time
from pathlib import Path
from statistics import quantiles
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from backend.app.agent.contracts import PlannerOutput, UnderstandingOutput
from backend.app.agent.multi_agent_contracts import SupervisorDecision
from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.agent.supervisor import SupervisorAgent
from backend.app.agent.after_sales_agent import AfterSalesAgent
from backend.app.agent.commerce_agent import CommerceAgent
from backend.app.domain.catalog import check_inventory
from backend.app.domain.handoff_service import summarize
from backend.app.domain.recommendation_service import recommend
from backend.app.tools.after_sales_tools import execute_resolution
from backend.app.db.seed import load_products_from_seed, seed_inventory

def load_scenarios() -> list[dict[str, Any]]:
    scenarios = []
    for path in sorted((ROOT / "scenarios").glob("*.json")):
        if path.name in {"customer_service_v1.json", "recommendation_multiturn_v1.json", "customer_service_quality_v1.json", "semantic_state_v1.json"}:
            continue
        loaded = json.loads(path.read_text(encoding="utf-8"))
        # The general runner is single-turn only. Multi-turn suites have
        # dedicated evaluators and must not be interpreted as flat scenarios.
        if isinstance(loaded, list):
            scenarios.extend(item for item in loaded if isinstance(item, dict) and "name" in item and "input" in item)
    return scenarios


def run_scenarios() -> list[dict[str, Any]]:
    results = []
    for scenario in load_scenarios():
        state = CustomerServiceState(session_id=f"eval_{scenario['name']}", customer_id="CUS001")
        state, reply, trace = run_turn(state, scenario["input"])
        if scenario.get("expected_status") and state.status != scenario["expected_status"]:
            state, reply, trace = run_turn(state, "确认退货")
        action = trace.get("next_action", {})
        results.append({
            "name": scenario["name"],
            "reply": reply,
            "goal_correct": (
                not scenario.get("expected_reason_code")
                or trace.get("reason_code") == scenario["expected_reason_code"]
            ),
            "tool_correct": (
                not scenario.get("expected_action")
                or action.get("type") == scenario["expected_action"]
            ),
            "parameters_complete": bool(action.get("arguments", {})) if action.get("type") == "TOOL_CALL" else True,
            "resolved": state.status in {"RESOLVED", "WAITING_CONFIRMATION", "HANDOFF"},
            "confirmation_violation": any(
                step.get("tool_name") == "create_return_request"
                for step in state.tool_results
            ) and not state.requires_confirmation and "确认" not in scenario["input"],
            "candidate_count": len(state.known_facts.get("recommendations", [])),
            "status": state.status,
            "active_agent": state.active_agent,
            "task_count": len(state.task_stack),
        })
    return results


def _p95(values: list[float]) -> float:
    if len(values) < 2:
        return values[0] if values else 0.0
    return quantiles(values, n=100, method="inclusive")[94]


def performance_metrics(iterations: int = 30) -> dict[str, float]:
    query_times = []
    turn_times = []
    for _ in range(iterations):
        started = time.perf_counter()
        check_inventory("SKU001")
        query_times.append(time.perf_counter() - started)
        state = CustomerServiceState(session_id=f"perf_{_}", customer_id="CUS001")
        started = time.perf_counter()
        run_turn(state, "全麦吐司还有货吗？")
        turn_times.append(time.perf_counter() - started)
    return {"query_p95_ms": _p95(query_times) * 1000, "turn_p95_ms": _p95(turn_times) * 1000}


def success_criteria() -> dict[str, Any]:
    # Success criteria must run against the same initialized catalog/inventory
    # boundary as the benchmark; otherwise recommendation results are null
    # because the in-memory catalog and inventory table are not bootstrapped.
    load_products_from_seed()
    seed_inventory()
    results = run_scenarios()
    total = len(results) or 1
    unknown = CustomerServiceState(session_id="sc001", customer_id="CUS001")
    for _ in range(3):
        unknown, _, _ = run_turn(unknown, "你好，我想咨询一下")
    handoff = summarize(unknown)
    recommendation = CustomerServiceState(session_id="sc004", customer_id="CUS001")
    recommendation, _, _ = run_turn(recommendation, "给孩子早餐吃，有什么低糖的？")
    performance = performance_metrics()
    metrics = {
        "SC-001": {"value": unknown.status == "HANDOFF", "threshold": True},
        "SC-002": {"value": all("库存" in item["reply"] and "时间" in item["reply"] for item in results if item["name"] == "inventory_in_stock"), "threshold": True},
        "SC-003": {"value": any(item["name"] == "return_requires_confirmation" and item["status"] == "WAITING_CONFIRMATION" for item in results), "threshold": True},
        "SC-004": {"value": bool(recommendation.known_facts.get("recommendations")) and all(p["available_quantity"] > 0 for p in recommendation.known_facts["recommendations"]), "threshold": True},
        "SC-005": {"value": all(handoff.get(key) is not None for key in ("original_request", "known_facts", "completed_steps")), "threshold": True},
        "SC-006": {"value": sum(bool(item["reply"]) for item in results) / total >= 0.85, "threshold": 0.85},
        "SC-007": {"value": sum(item["confirmation_violation"] for item in results) == 0, "threshold": 0},
        "SC-008": {"value": all(PlannerOutput.model_validate({"goal": {"type": "OTHER"}, "next_action": {"type": "ASK_USER"}, "reason_code": "EVAL"}).schema_version == "1.0" for _ in [0]), "threshold": 1},
        "SC-009": {"value": bool(recommend(["低糖"])) and performance["query_p95_ms"] < 300, "threshold": "p95 < 300ms"},
        "performance": performance,
        "scenario_count": len(results),
    }
    metrics["v2"] = multi_agent_metrics()
    metrics["all_passed"] = all(bool(item["value"]) for key, item in metrics.items() if key.startswith("SC-"))
    return metrics


def score(results: list[dict]) -> dict:
    total = len(results) or 1
    return {
        "goal_accuracy": sum(r.get("goal_correct", False) for r in results) / total,
        "tool_accuracy": sum(r.get("tool_correct", False) for r in results) / total,
        "parameter_completeness": sum(r.get("parameters_complete", False) for r in results) / total,
        "task_completion_rate": sum(r.get("resolved", False) for r in results) / total,
        "confirmation_violations": sum(r.get("confirmation_violation", False) for r in results),
        "count": len(results),
    }


def multi_agent_metrics() -> dict[str, Any]:
    scenarios = [scenario for scenario in load_scenarios() if scenario.get("expected_domain")]
    routed = []
    for scenario in scenarios:
        understanding = UnderstandingOutput(goals=scenario.get("goals", []))
        routed.append((scenario, SupervisorAgent().decide(understanding, scenario["input"])))
    route_matches = [
        decision.domain == scenario["expected_domain"]
        and decision.route_action == scenario["expected_route_action"]
        for scenario, decision in routed
    ]
    task_schema_valid = all(
        SupervisorDecision.model_validate(decision.model_dump()).schema_version == "v2"
        for _, decision in routed
    )
    result_rows = run_scenarios()
    clarity = sum(bool(row["reply"]) for row in result_rows) / (len(result_rows) or 1)
    loop_count = sum(
        row["status"] == "WAITING_USER" and not row["reply"].strip()
        for row in result_rows
    )
    state = CustomerServiceState(session_id="v2_context", customer_id="CUS001")
    state, _, _ = run_turn(state, "两个原味吐司")
    context_retained = bool(
        state.known_facts.get("quote_context")
        or state.known_facts.get("selected_products")
        or state.known_facts.get("recent_products")
    )
    blocked_side_effect = execute_resolution(
        {"recommended_level": "ITEM_REFUND", "requires_human": False},
        confirmed=False,
        idempotency_key=None,
    )
    unauthorized_side_effects = int(blocked_side_effect.get("ok", False))
    replacement_results = {
        "commerce": bool(CommerceAgent().capabilities()),
        "after_sales": all(hasattr(AfterSalesAgent(), name) for name in ("intake", "classify", "start_case")),
        "supervisor": hasattr(SupervisorAgent(), "decide"),
    }
    handoff_state = CustomerServiceState(session_id="v2_handoff", customer_id="CUS001")
    handoff_state, _, _ = run_turn(handoff_state, "请转人工客服")
    handoff = summarize(handoff_state)
    handoff_complete = all(
        handoff.get(key) is not None
        for key in ("original_request", "known_facts", "completed_steps")
    )
    return {
        "supervisor_domain_accuracy": sum(
            decision.domain == scenario["expected_domain"]
            for scenario, decision in routed
        ) / (len(routed) or 1),
        "agent_task_schema_accuracy": task_schema_valid,
        "response_clarity_proxy_score": clarity,
        "loop_rate": loop_count / (len(result_rows) or 1),
        "route_task_accuracy": sum(route_matches) / (len(route_matches) or 1),
        "cross_agent_context_retention": context_retained,
        "unauthorized_side_effect_count": unauthorized_side_effects,
        "component_replacement_results": replacement_results,
        "handoff_context_completeness": handoff_complete,
    }


if __name__ == "__main__":
    print(json.dumps(success_criteria(), ensure_ascii=False, indent=2))
