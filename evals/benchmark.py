from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from statistics import quantiles
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT.parent / ".env")
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))

from backend.app.agent.graph import run_turn
from backend.app.agent.state import CustomerServiceState
from backend.app.domain.business_config import snapshot
from backend.app.domain.inventory_service import get_service
from backend.app.domain.reservation_service import clear_reservations
from backend.app.db.seed import load_products_from_seed
from benchmark_assertions import bootstrap_fixture, score_case, assert_followup_recovery
from judge import judge_case


def load_cases(suite: str) -> list[dict[str, Any]]:
    path = ROOT / "scenarios" / f"{suite}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    # Scenario suites may carry metadata alongside the case list.
    cases = payload.get("cases", []) if isinstance(payload, dict) else payload
    if not isinstance(cases, list):
        raise RuntimeError("FIXTURE_SETUP_FAILED: scenario cases must be a list")
    expected_count = {"customer_service_v1": 20, "customer_service_quality_v1": 20, "followup_accuracy_v1": 20, "real_group_orders_v1": 8}.get(suite)
    if expected_count is not None and len(cases) != expected_count:
        raise RuntimeError(f"FIXTURE_SETUP_FAILED: expected {expected_count} cases, got {len(cases)}")
    ids = [case.get("id") for case in cases]
    prefix = "SC-" if suite == "customer_service_v1" else ("CQ-" if suite == "customer_service_quality_v1" else ("RS-" if suite == "reference_state_v1" else ("FQ-" if suite == "followup_accuracy_v1" else ("FR-" if suite == "followup_recovery_v1" else ("RG-" if suite == "real_group_orders_v1" else "SS-")))))
    if len(set(ids)) != len(ids) or any(not item.startswith(prefix) for item in ids):
        raise RuntimeError("FIXTURE_SETUP_FAILED: invalid case ids")
    return cases


def run_case(case: dict[str, Any], fixture: dict[str, Any]) -> dict[str, Any]:
    if case["id"].startswith("RG-"):
        # The persisted admin snapshot may predate this fixture's products.
        load_products_from_seed()
    if case.get("fixture", {}).get("inventory"):
        for product_id, values in case["fixture"]["inventory"].items():
            get_service().adjust(product_id, values["on_hand"], values.get("reserved", 0), reason="BENCHMARK_CASE_RESET", actor="benchmark")
    clear_reservations()
    state = CustomerServiceState(session_id=f"benchmark_{case['id']}", customer_id="CUS001")
    states, traces, replies, state_snapshots = [], [], [], []
    started = time.perf_counter()
    try:
        for turn in case["turns"]:
            state, reply, trace = run_turn(state, turn["user"])
            states.append(state.model_copy(deep=True))
            state_snapshots.append({
                "turn": len(states),
                "selected_products": state.known_facts.get("selected_products", []),
                "quote_context": state.quote_context.model_dump() if state.quote_context else None,
                "focused_product": state.focused_product,
                "recommendation_candidates": state.recommendation_candidates,
            })
            traces.append(trace)
            replies.append(reply)
        result = score_case(case, states, traces, replies, fixture)
        result["state_snapshots"] = state_snapshots
        result["lineage"] = [step for trace in traces for step in trace.get("lineage", [])] + [
            step for trace in traces for step in trace.get("steps", [])
        ]
        result["feedback_events"] = [event for snapshot in states for event in snapshot.feedback_events]
        if case.get("expected", {}).get("accepted_action") == "recommend_products":
            result["followup_assertions"] = assert_followup_recovery(states[-1], traces[-1], replies[-1])
        result["component_scores"] = states[-1].turn_evaluations[-1].get("component_scores", {}) if states and states[-1].turn_evaluations else {}
        result["failure_component"] = states[-1].turn_evaluations[-1].get("failure_component") if states and states[-1].turn_evaluations else None
        result["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
        result["status"] = state.status
        result["judge"] = None if os.getenv("BENCHMARK_SKIP_JUDGE") == "1" else judge_case(case, result)
        return result
    except Exception as exc:
        return {
            "id": case["id"], "turns": case["turns"], "scores": {"goal": 0, "entity": 0, "tool": 0, "business_result": 0, "response_safety": 0},
            "total": 0, "status": "BENCHMARK_ERROR", "error": type(exc).__name__,
            "fixture_version": fixture["fixture_version"], "latency_ms": round((time.perf_counter() - started) * 1000, 2),
        }


def run_variant(cases: list[dict[str, Any]], fixture: dict[str, Any], architecture: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    previous = os.environ.get("AGENT_ARCHITECTURE")
    os.environ["AGENT_ARCHITECTURE"] = architecture
    try:
        results = [run_case(case, fixture) for case in cases]
        return results, aggregate(results)
    finally:
        if previous is None:
            os.environ.pop("AGENT_ARCHITECTURE", None)
        else:
            os.environ["AGENT_ARCHITECTURE"] = previous


def aggregate(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results) or 1
    def rate(key: str) -> float:
        return round(sum(item["scores"].get(key, 0) for item in results) / total, 4)
    all_tools = [tool for item in results for tool in item.get("tools", [])]
    # A multi-turn case may legitimately execute one tool per turn. The old
    # case-level denominator inflated unnecessary_tool_rate for valid re-plans.
    expected_tool_cases = sum(max(1, len(item.get("turns", []))) for item in results if item.get("tools"))
    forbidden_count = sum(1 for item in results for tool in item.get("tools", []) if tool in {"list_available_inventory"} and item["id"] == "SC-04")
    latencies = sorted(item.get("latency_ms", 0) for item in results)
    p95 = latencies[min(len(latencies) - 1, max(0, int(len(latencies) * 0.95) - 1))] if latencies else 0
    component_values: dict[str, list[str]] = {}
    for item in results:
        for component, status in item.get("component_scores", {}).items():
            if status != "NOT_RUN":
                component_values.setdefault(component, []).append(status)
    component_accuracy = {
        component.lower(): round(sum(status == "PASS" for status in statuses) / len(statuses), 4)
        for component, statuses in component_values.items() if statuses
    }
    failures = {}
    for item in results:
        component = item.get("failure_component")
        if component:
            failures[component] = failures.get(component, 0) + 1
    clarification_cases = [item.get("clarification", {}) for item in results]
    followup_ids = {f"FQ-{index:02d}" for index in range(1, 21)}
    quote_ids = {f"FQ-{index:02d}" for index in (1, 2, 4, 5, 6, 8, 12, 13, 18)}
    return {
        "overall_score": round(sum(item.get("total", 0) for item in results) / (total * 5) * 100, 2),
        "goal_accuracy": rate("goal"), "entity_accuracy": rate("entity"), "tool_precision": rate("tool"),
        "business_accuracy": rate("business_result"), "response_clarity_score": rate("response_safety"),
        "task_completion_rate": round(sum(item.get("status") not in {"BENCHMARK_ERROR", "FAILED"} for item in results) / total, 4),
        "unnecessary_tool_rate": round(max(0, len(all_tools) - expected_tool_cases) / (len(all_tools) or 1), 4),
        "forbidden_tool_call_count": forbidden_count,
        "clarification_count": sum(item.get("clarification_count", 0) for item in clarification_cases),
        "selection_detection_rate": round(sum(bool(item.get("selection_detected")) for item in clarification_cases) / total, 4),
        "blocked_delivery_side_effect_count": sum(item.get("blocked_side_effect_count", 0) for item in clarification_cases),
        "wrong_fallback_rate": round(sum("LLM_OUTPUT_INVALID" in " ".join(item.get("replies", [])) for item in results) / total, 4),
        "multi_turn_state_consistency": round(sum(item.get("state_mutation_score", item.get("scores", {}).get("business_result", 0)) for item in results if item["id"] in followup_ids) / max(1, len([item for item in results if item["id"] in followup_ids])), 4),
        "quote_recalculation_accuracy": round(sum(item.get("scores", {}).get("business_result", 0) for item in results if item["id"] in quote_ids) / max(1, len([item for item in results if item["id"] in quote_ids])), 4),
        "recommendation_constraint_accuracy": round(sum(item.get("scores", {}).get("business_result", 0) for item in results if item["id"] in {"SC-11","SC-12","SC-13"}) / 3, 4),
        "p95_latency_ms": p95,
        "tool_call_count": len(all_tools),
        "component_accuracy": component_accuracy,
        "first_failure_components": failures,
        "feedback_correction_rate": round(sum(bool(item.get("feedback_events")) for item in results) / total, 4),
        "semantic_state_coverage": round(sum(bool(item.get("component_scores")) for item in results) / total, 4),
        "reservation_state_accuracy": round(sum(item.get("scores", {}).get("business_result", 0) for item in results if item["id"].startswith("RG-")) / max(1, len([item for item in results if item["id"].startswith("RG-")])), 4),
        "inventory_safety_rate": round(sum(item.get("scores", {}).get("business_result", 0) for item in results if item["id"].startswith("RG-")) / max(1, len([item for item in results if item["id"].startswith("RG-")])), 4),
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [f"# Customer Service Agent Benchmark V1", "", f"- Run: {report['run_at']}", f"- Model: {report['model']}", f"- Fixture: {report['fixture_version']}", "", "## Metrics", ""]
    if report.get("comparison"):
        lines += ["## Legacy vs Semantic", "", f"- Legacy overall: {report['variants']['legacy']['metrics']['overall_score']}", f"- Semantic overall: {report['variants']['semantic']['metrics']['overall_score']}", f"- Score delta: {report['comparison']['score_delta']}", f"- Repeated clarification delta: {report['comparison']['repeated_clarification_delta']}", f"- Premature handoff delta: {report['comparison']['premature_handoff_delta']}", ""]
    for key, value in report["metrics"].items():
        lines.append(f"- {key}: {value}")
    lines += ["", "## Case Results", "", "| Case | Score | Status | Tools |", "|---|---:|---|---|"]
    for item in report["cases"]:
        lines.append(f"| {item['id']} | {item.get('total', 0)}/5 | {item.get('status', '')} | {', '.join(item.get('tools', []))} |")
    failures = [item for item in report["cases"] if item.get("total", 0) < 5]
    lines += ["", "## Component Evaluation", ""]
    for component, value in report["metrics"].get("component_accuracy", {}).items():
        lines.append(f"- {component}: {value}")
    lines += ["", "## Failures", ""]
    lines.extend(f"- {item['id']}: {item.get('scores')} {item.get('business_detail', {})}" for item in failures) or lines.append("- None")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="customer_service_v1")
    parser.add_argument("--output-dir", default="reports/benchmark")
    parser.add_argument("--compare", action="store_true", help="run legacy and semantic architectures against the same cases")
    parser.add_argument("--no-judge", action="store_true", help="skip language-quality Judge calls")
    parser.add_argument("--case", help="comma-separated case IDs to run")
    args = parser.parse_args()
    if args.no_judge:
        os.environ["BENCHMARK_SKIP_JUDGE"] = "1"
    try:
        fixture = bootstrap_fixture()
        cases = load_cases(args.suite)
        if args.case:
            wanted = {item.strip() for item in args.case.split(",") if item.strip()}
            cases = [case for case in cases if case.get("id") in wanted]
    except Exception as exc:
        print(json.dumps({"status": "FIXTURE_SETUP_FAILED", "error": str(exc)}, ensure_ascii=False))
        return 2
    if args.compare:
        legacy_cases, legacy_metrics = run_variant(cases, fixture, "legacy")
        semantic_cases, semantic_metrics = run_variant(cases, fixture, "semantic")
        results = semantic_cases
        metrics = semantic_metrics
        comparison = {
            "score_delta": round(semantic_metrics["overall_score"] - legacy_metrics["overall_score"], 2),
            "goal_or_intent_delta": round(semantic_metrics["goal_accuracy"] - legacy_metrics["goal_accuracy"], 4),
            "reference_resolution_delta": round(semantic_metrics.get("entity_accuracy", 0) - legacy_metrics.get("entity_accuracy", 0), 4),
            "business_accuracy_delta": round(semantic_metrics["business_accuracy"] - legacy_metrics["business_accuracy"], 4),
            "repeated_clarification_delta": round(semantic_metrics.get("clarification_count", 0) - legacy_metrics.get("clarification_count", 0), 2),
            "premature_handoff_delta": round(sum(item.get("status") == "HANDOFF" for item in semantic_cases) - sum(item.get("status") == "HANDOFF" for item in legacy_cases), 2),
            "latency_delta_ms": round(semantic_metrics["p95_latency_ms"] - legacy_metrics["p95_latency_ms"], 2),
        }
    else:
        results = [run_case(case, fixture) for case in cases]
        metrics = aggregate(results)
        legacy_metrics = None
        semantic_metrics = None
        comparison = None
    report = {
        "suite": args.suite, "run_at": datetime.now(timezone.utc).isoformat(),
        "model": os.getenv("LLM_MODEL", "deepseek-chat"), "fixture_version": fixture["fixture_version"],
        "fixture_summary": {"product_count": fixture["product_count"], "policy": fixture.get("sales_policy", {})},
        "metrics": metrics, "cases": results,
        "passed": metrics["overall_score"] >= 90 and metrics["forbidden_tool_call_count"] == 0,
    }
    if args.compare:
        report["variants"] = {"legacy": {"metrics": legacy_metrics, "cases": legacy_cases}, "semantic": {"metrics": semantic_metrics, "cases": semantic_cases}}
        report["comparison"] = comparison
    output = Path(args.output_dir); output.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    (output / f"{args.suite}_{stamp}.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / f"{args.suite}_{stamp}.md").write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps({"status": "PASS" if report["passed"] else "FAIL", "metrics": metrics}, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
