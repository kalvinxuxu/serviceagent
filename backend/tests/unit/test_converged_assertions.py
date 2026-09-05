import pytest

from evals.converged_assertions import architecture_metrics, assert_converged_metrics


def test_architecture_metrics_detect_no_duplicate_decisions():
    metrics = architecture_metrics([
        {"decision_id": "a", "step_count": 3, "legacy_tool_count": 2, "converged_tool_count": 1},
        {"decision_id": "b", "step_count": 2, "legacy_tool_count": 2, "converged_tool_count": 1},
    ])
    assert metrics["duplicate_decision_count"] == 0
    assert metrics["tool_surface_reduction"] == 0.5


def test_architecture_assertions_reject_duplicate_decisions():
    metrics = architecture_metrics([{"decision_id": "same"}, {"decision_id": "same"}])
    with pytest.raises(AssertionError):
        assert_converged_metrics(metrics)
