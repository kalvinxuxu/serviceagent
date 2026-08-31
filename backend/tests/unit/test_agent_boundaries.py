from backend.app.agent.commerce_capabilities import COMMERCE_CAPABILITIES
from backend.app.agent.supervisor_router import build_tasks


def test_mixed_goals_produce_explicit_tasks_and_no_supervisor_tools():
    tasks = build_tasks(["PRICE_CALCULATION", "INVENTORY_CHECK"])
    assert len(tasks) == 2
    assert {task.target_agent for task in tasks} == {"COMMERCE"}
    assert set(COMMERCE_CAPABILITIES).isdisjoint({"refund", "create_return_request", "update_inventory"})
