from ..agent.multi_agent_contracts import EvidenceObservation


def observe_text(text: str, classification: str = "CUSTOMER_CLAIM") -> EvidenceObservation:
    return EvidenceObservation(source="TEXT", classification=classification, confidence=1.0, observed_facts=[text], observed_at="runtime")


def observe_image(metadata: dict) -> EvidenceObservation:
    return EvidenceObservation(source="IMAGE", classification="UNCLASSIFIED", confidence=0.0, observed_at="runtime", uncertainties=["vision_provider_unavailable"])
