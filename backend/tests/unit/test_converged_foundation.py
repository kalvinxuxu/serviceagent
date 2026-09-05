import importlib

from backend.app.agent.lineage import first_failure, mark_downstream_not_run


def test_lineage_identifies_first_failure_and_blocks_stale_downstream_passes():
    steps = [
        {"component": "SEMANTIC_UNDERSTANDING", "status": "FAIL"},
        {"component": "ACTION_PLANNER", "status": "PASS"},
        {"component": "EXECUTOR", "status": "PASS"},
    ]
    assert first_failure(steps) == "SEMANTIC_UNDERSTANDING"
    assert [step["status"] for step in mark_downstream_not_run(steps, first_failure(steps))] == ["FAIL", "NOT_RUN", "NOT_RUN"]


def test_config_accepts_converged_mode(monkeypatch):
    monkeypatch.setenv("AGENT_ARCHITECTURE", "converged")
    module = importlib.reload(importlib.import_module("backend.app.config"))
    assert module.AGENT_ARCHITECTURE == "converged"
