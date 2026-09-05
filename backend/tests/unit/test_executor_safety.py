from backend.app.agent.contracts import ExecutionDecision
from backend.app.agent.executor import ActionExecutor


def test_executor_blocks_unconfirmed_side_effect(monkeypatch):
    called = False

    def fail_if_called(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("backend.app.agent.executor.execute", fail_if_called)
    result = ActionExecutor().execute(ExecutionDecision(
        kind="TOOL_CALL", action="RETURN", tool_name="create_return_request", reason_code="R",
    ))
    assert result.ok is False
    assert result.reason == "CONFIRMATION_REQUIRED"
    assert called is False
