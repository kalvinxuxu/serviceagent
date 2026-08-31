import pytest
from pydantic import ValidationError

from backend.app.agent.multi_agent_contracts import (
    AgentTask,
    EvidenceObservation,
    ResolutionDecision,
    SupervisorDecision,
)


def test_supervisor_decision_requires_tasks_for_agent_route():
    with pytest.raises(ValidationError):
        SupervisorDecision(goals=["INVENTORY_CHECK"], domain="COMMERCE", route_action="SWITCH_AGENT", reason_code="R", confidence=0.9)


def test_supervisor_ask_user_requires_missing_information():
    with pytest.raises(ValidationError):
        SupervisorDecision(goals=["OTHER"], domain="UNKNOWN", route_action="ASK_USER", reason_code="R", confidence=0.5)


def test_blocked_task_requires_reason_and_route_tasks_validate():
    with pytest.raises(ValidationError):
        AgentTask(id="t1", session_id="s1", task_type="HANDLE", source_agent="SUPERVISOR", target_agent="COMMERCE", status="BLOCKED")


def test_evidence_cannot_authorize_side_effect_and_resolution_requires_confirmation():
    observation = EvidenceObservation(source="IMAGE", classification="DAMAGED_PRODUCT", confidence=0.9, observed_at="now")
    assert observation.side_effect_allowed is False
    with pytest.raises(ValidationError):
        ResolutionDecision(issue_type="DAMAGED_PRODUCT", policy_version="1", allowed_levels=["ITEM_REFUND"], recommended_level="ITEM_REFUND", requires_confirmation=False, reason_code="POLICY")
