from backend.app.agent.contracts import ExecutionDecision
from backend.app.agent.executor import ActionExecutor
from backend.app.agent.plan_validator import validate_execution_decision


def test_policy_capability_check_precedes_executor(monkeypatch):
    decision = ExecutionDecision(kind="TOOL_CALL", action="CHECK", tool_name="check_inventory", arguments={"product_id": "SKU001"}, reason_code="R")
    assert validate_execution_decision(decision, {"check_inventory"}) is decision
    monkeypatch.setattr("backend.app.agent.executor.execute", lambda *_: None)
    assert ActionExecutor().execute(decision) is None
