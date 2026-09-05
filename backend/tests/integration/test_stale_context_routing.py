from backend.app.agent.state import CustomerServiceState
from backend.app.agent.supervisor import SupervisorAgent
from backend.app.agent.contracts import UnderstandingOutput


def test_new_commerce_turn_does_not_inherit_human_domain():
    state = CustomerServiceState(session_id="stale-context", active_domain="UNKNOWN", execution_mode="HUMAN_HANDOFF")
    decision = SupervisorAgent().decide_domain(UnderstandingOutput(goals=["INVENTORY_CHECK"]), "查询库存")
    assert decision.domain == "COMMERCE"
    assert state.active_domain == "UNKNOWN"
