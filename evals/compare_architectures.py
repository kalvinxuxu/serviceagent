from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from benchmark import aggregate, bootstrap_fixture, load_cases, run_variant


def compare_suite(suite: str) -> dict:
    fixture = bootstrap_fixture()
    cases = load_cases(suite)
    legacy_cases, legacy = run_variant(cases, fixture, "legacy")
    semantic_cases, semantic = run_variant(cases, fixture, "converged")
    return {
        "suite": suite,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "fixture_version": fixture["fixture_version"],
        "variants": {"legacy": {"metrics": legacy, "cases": legacy_cases}, "semantic": {"metrics": semantic, "cases": semantic_cases}},
        "comparison": {
            "score_delta": round(semantic["overall_score"] - legacy["overall_score"], 2),
            "reference_resolution_delta": round(semantic.get("entity_accuracy", 0) - legacy.get("entity_accuracy", 0), 4),
            "state_mutation_delta": round(semantic.get("multi_turn_state_consistency", 0) - legacy.get("multi_turn_state_consistency", 0), 4),
            "business_accuracy_delta": round(semantic["business_accuracy"] - legacy["business_accuracy"], 4),
            "premature_handoff_delta": sum(item.get("status") == "HANDOFF" for item in semantic_cases) - sum(item.get("status") == "HANDOFF" for item in legacy_cases),
            "repeated_clarification_delta": semantic.get("clarification_count", 0) - legacy.get("clarification_count", 0),
            "latency_delta_ms": round(semantic.get("p95_latency_ms", 0) - legacy.get("p95_latency_ms", 0), 2),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="followup_accuracy_v1")
    parser.add_argument("--output", default="reports/benchmark/architecture_comparison.json")
    args = parser.parse_args()
    report = compare_suite(args.suite)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report["comparison"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
