from evals.converged_assertions import architecture_metrics


def test_architecture_comparison_reports_tool_and_step_deltas():
    metrics = architecture_metrics([
        {"decision_id": "a", "step_count": 3, "legacy_tool_count": 2, "converged_tool_count": 1},
    ])
    assert metrics["average_step_count"] == 3
    assert metrics["tool_surface_reduction"] == 0.5
