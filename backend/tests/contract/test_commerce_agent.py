from backend.app.agent.commerce_agent import CommerceAgent
from backend.app.agent.multi_agent_contracts import AgentTask
from backend.app.agent.state import CustomerServiceState


def test_commerce_agent_accepts_only_commerce_tasks_and_exposes_allowlist():
    task = AgentTask(id="c1", session_id="s1", task_type="COMMERCE", source_agent="SUPERVISOR", target_agent="COMMERCE")
    result = CommerceAgent().intake(task, CustomerServiceState(session_id="s1"))
    assert "calculate_order_quote" in result["capabilities"]
    assert "refund" not in result["capabilities"]


def test_commerce_agent_rejects_after_sales_task():
    task = AgentTask(id="a1", session_id="s1", task_type="AFTER_SALES", source_agent="SUPERVISOR", target_agent="AFTER_SALES")
    result = CommerceAgent().intake(task, CustomerServiceState(session_id="s1"))
    assert result["ok"] is False
