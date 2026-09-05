from __future__ import annotations

from .contracts import TurnEvaluation


ORDER = (
    "UNDERSTANDING", "FOLLOWUP_INTENT_RESOLVER", "NORMALIZATION", "ENTITY_RESOLVER",
    "CONSTRAINT_EXTRACTION", "GOAL_MANAGER", "CAPABILITY_RESOLVER", "PLANNER",
    "PLAN_VALIDATOR", "TOOL_SELECTION", "TOOL_ARGUMENTS", "BUSINESS_SERVICE",
    "STATE_MANAGER", "RESPONSE_GENERATION",
)

INVALID_REASONS = {"LLM_OUTPUT_INVALID", "SEMANTIC_INTENT_UNRESOLVED", "ACCEPT_FOLLOWUP_NOT_RESOLVED"}


def evaluate_turn(state, trace: dict | None = None) -> TurnEvaluation:
    trace = trace or {}
    reason = trace.get("reason_code")
    understanding_ok = state.known_facts.get("understanding_status") == "VALID"
    upstream_failure = reason in INVALID_REASONS or not understanding_ok
    action = trace.get("next_action") or {}
    tool_result = state.tool_results[-1] if state.tool_results else None
    scores = {component: "NOT_RUN" for component in ORDER}

    scores["UNDERSTANDING"] = "FAIL" if upstream_failure else "PASS"
    if not upstream_failure:
        scores["FOLLOWUP_INTENT_RESOLVER"] = "PASS" if state.known_facts.get("followup_intent") or not state.pending_followup else "NOT_RUN"
        scores["NORMALIZATION"] = "PASS" if state.semantic_state else "NOT_RUN"
        understanding = state.known_facts.get("understanding", {})
        requested = understanding.get("requested_items", [])
        resolved = state.known_facts.get("resolved_products") or []
        resolved_count = sum(1 for item in resolved if item.get("product_id"))
        if requested and resolved_count < len(requested):
            scores["ENTITY_RESOLVER"] = "FAIL"
        elif requested:
            scores["ENTITY_RESOLVER"] = "PASS"
        else:
            scores["ENTITY_RESOLVER"] = "NOT_RUN"
        scores["CONSTRAINT_EXTRACTION"] = "PASS" if state.known_facts.get("understanding", {}).get("constraints") is not None else "NOT_RUN"
        scores["GOAL_MANAGER"] = "PASS" if state.goals else "NOT_RUN"
        scores["CAPABILITY_RESOLVER"] = "PASS" if state.known_facts.get("capabilities") is not None else "NOT_RUN"
        scores["PLANNER"] = "PASS" if action else "NOT_RUN"
        scores["PLAN_VALIDATOR"] = "FAIL" if reason == "CAPABILITY_NOT_ALLOWED" else ("PASS" if action else "NOT_RUN")
        scores["TOOL_SELECTION"] = "PASS" if action.get("type") != "TOOL_CALL" or action.get("tool_name") else "FAIL"
        scores["TOOL_ARGUMENTS"] = "PASS" if action.get("type") != "TOOL_CALL" or isinstance(action.get("arguments"), dict) else "FAIL"
        scores["BUSINESS_SERVICE"] = "PASS" if tool_result and tool_result.get("ok") else ("FAIL" if tool_result else "NOT_RUN")
        scores["STATE_MANAGER"] = "PASS" if state.state_version >= 1 else "FAIL"
        if state.known_facts.get("slot_update_status") == "UNCHANGED" and state.missing_slots:
            scores["STATE_MANAGER"] = "FAIL"
        scores["RESPONSE_GENERATION"] = "PASS" if trace.get("status") not in {"FAILED", "HANDOFF"} else "FAIL"
    else:
        scores["RESPONSE_GENERATION"] = "FAIL"

    # An upstream failure prevents downstream components from being assessed.
    # This avoids reporting a successful business call or response when the
    # planner only produced a fallback/clarification.
    first_failure = next((component for component in ORDER if scores[component] == "FAIL"), None)
    if first_failure:
        for component in ORDER[ORDER.index(first_failure) + 1:]:
            scores[component] = "NOT_RUN"

    failure = next((component for component in ORDER if scores[component] == "FAIL"), None)
    return TurnEvaluation(
        understanding_confidence=0.0 if upstream_failure else 1.0,
        goal_confidence=0.0 if upstream_failure else (1.0 if state.goals else 0.0),
        entity_resolution=scores["ENTITY_RESOLVER"],
        constraint_extraction=scores["CONSTRAINT_EXTRACTION"],
        tool_execution=scores["BUSINESS_SERVICE"],
        business_result_status=scores["BUSINESS_SERVICE"],
        response_grounded=scores["RESPONSE_GENERATION"] == "PASS",
        requires_followup=state.status in {"WAITING_USER", "WAITING_SELECTION", "WAITING_CONFIRMATION"},
        failure_component=failure,
        component_scores=scores,
    )
