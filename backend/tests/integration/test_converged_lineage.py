from backend.app.agent.lineage import first_failure, mark_downstream_not_run


def test_first_failure_marks_only_downstream_pass_steps_not_run():
    steps = [
        {"component": "SEMANTIC_UNDERSTANDING", "status": "PASS"},
        {"component": "REFERENCE_RESOLVER", "status": "FAIL"},
        {"component": "EXECUTOR", "status": "PASS"},
    ]
    assert first_failure(steps) == "REFERENCE_RESOLVER"
    assert mark_downstream_not_run(steps, "REFERENCE_RESOLVER")[2]["status"] == "NOT_RUN"
