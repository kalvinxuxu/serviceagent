"""Executable assertions for the Converged architecture boundaries."""

from __future__ import annotations

from collections import Counter
from typing import Any


def architecture_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize decision duplication, unnecessary steps, and handoff leakage."""
    total = len(rows) or 1
    decisions = [row.get("decision_id") or row.get("reason_code") for row in rows]
    duplicate_decisions = len(decisions) - len(set(decisions))
    return {
        "count": len(rows),
        "duplicate_decision_count": duplicate_decisions,
        "unnecessary_tool_rate": sum(bool(row.get("unnecessary_tool")) for row in rows) / total,
        "premature_handoff_rate": sum(bool(row.get("premature_handoff")) for row in rows) / total,
        "average_step_count": sum(row.get("step_count", 0) for row in rows) / total,
        "tool_surface_reduction": row_tool_surface_reduction(rows),
    }


def row_tool_surface_reduction(rows: list[dict[str, Any]]) -> float:
    before = sum(row.get("legacy_tool_count", 0) for row in rows)
    after = sum(row.get("converged_tool_count", 0) for row in rows)
    return 0.0 if before == 0 else round((before - after) / before, 4)


def assert_converged_metrics(metrics: dict[str, Any]) -> None:
    assert metrics["duplicate_decision_count"] == 0
    assert metrics["unnecessary_tool_rate"] <= 0.05
    assert metrics["premature_handoff_rate"] <= 0.05
