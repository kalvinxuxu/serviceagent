from typing import Any

from .multi_agent_contracts import ComplaintContext, EvidenceObservation


def complaint_snapshot(context: ComplaintContext) -> dict[str, Any]:
    return {"complaint_context": context.model_dump(), "evidence_observations": []}


def append_observation(snapshot: dict[str, Any], observation: EvidenceObservation) -> dict[str, Any]:
    updated = dict(snapshot)
    updated.setdefault("evidence_observations", []).append(observation.model_dump())
    return updated
