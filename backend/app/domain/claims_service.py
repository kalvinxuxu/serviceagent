from typing import Any

from ..agent.after_sales_state import append_observation, complaint_snapshot
from ..agent.multi_agent_contracts import ComplaintContext, EvidenceObservation


def create_complaint(issue_type: str, claim: str, order_id: str | None = None) -> dict[str, Any]:
    context = ComplaintContext(issue_type=issue_type, customer_claim=claim, order_id=order_id)
    return complaint_snapshot(context)


def add_evidence(snapshot: dict[str, Any], observation: EvidenceObservation) -> dict[str, Any]:
    return append_observation(snapshot, observation)
