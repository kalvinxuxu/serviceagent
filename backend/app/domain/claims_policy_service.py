from ..agent.multi_agent_contracts import ComplaintContext, ResolutionDecision


def evaluate_claim(context: ComplaintContext, policy_version: str = "claims-v1") -> ResolutionDecision:
    if context.safety_risk or context.severity == "HIGH":
        level, allowed, requires_human = "HUMAN_APPROVAL", ["HUMAN_APPROVAL"], True
    elif context.evidence_status in {"INSUFFICIENT", "CONFLICTING", "REQUESTED"}:
        level, allowed, requires_human = "EXPLAIN", ["EXPLAIN", "HUMAN_APPROVAL"], False
    elif context.issue_type == "DAMAGED_PRODUCT":
        level, allowed, requires_human = "REPLACEMENT", ["EXPLAIN", "REPLACEMENT", "ITEM_REFUND", "HUMAN_APPROVAL"], False
    else:
        level, allowed, requires_human = "EXPLAIN", ["EXPLAIN", "HUMAN_APPROVAL"], False
    return ResolutionDecision(
        issue_type=context.issue_type, policy_version=policy_version,
        allowed_levels=allowed, recommended_level=level,
        options=[{"level": item} for item in allowed],
        requires_confirmation=level != "EXPLAIN", requires_human=requires_human,
        reason_code="CLAIMS_POLICY_EVALUATED",
    )
