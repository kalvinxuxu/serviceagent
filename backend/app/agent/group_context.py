from __future__ import annotations

from copy import deepcopy
from typing import Any

from .state import CustomerServiceState
from .contracts import QuoteContext, PendingFollowup

PRIVATE_FIELDS = (
    "known_facts", "missing_fields", "current_plan", "tool_results", "requires_confirmation",
    "requires_human", "status", "original_request", "completed_steps", "pending_items",
    "quote_context", "current_order", "complaint_context", "active_agent", "task_stack",
    "handoff_history", "semantic_state", "feedback_events", "turn_evaluations", "conversation_act",
    "missing_slots", "delivery_slots", "delivery_mode", "pending_evidence", "evidence_history",
    "logistics_context", "pending_followup", "pending_followup_history",
)
SHARED_FACT_KEYS = {"recommendations", "recommendation_context", "available_products", "comparison", "sales_policy"}


def _dump(value: Any) -> Any:
    return value.model_dump() if hasattr(value, "model_dump") else deepcopy(value)


def _snapshot(state: CustomerServiceState) -> dict[str, Any]:
    data = {field: _dump(getattr(state, field)) for field in PRIVATE_FIELDS}
    data["known_facts"] = {key: deepcopy(value) for key, value in state.known_facts.items() if key not in SHARED_FACT_KEYS}
    return data


def _shared_facts(state: CustomerServiceState) -> dict[str, Any]:
    return {key: deepcopy(value) for key, value in state.known_facts.items() if key in SHARED_FACT_KEYS}


def activate_customer(state: CustomerServiceState, customer_id: str) -> None:
    if state.active_customer_id:
        state.customer_contexts[state.active_customer_id] = _snapshot(state)
    saved = state.customer_contexts.get(customer_id)
    defaults = CustomerServiceState(session_id=state.session_id, customer_id=customer_id)
    if saved:
        for field in PRIVATE_FIELDS:
            if field == "known_facts":
                continue
            value = deepcopy(saved.get(field, getattr(defaults, field)))
            if field == "quote_context" and isinstance(value, dict):
                value = QuoteContext.model_validate(value)
            if field == "pending_followup" and isinstance(value, dict):
                value = PendingFollowup.model_validate(value)
            setattr(state, field, value)
        state.known_facts = {**_shared_facts(state), **deepcopy(saved.get("known_facts", {}))}
    else:
        state.known_facts = _shared_facts(state)
    state.customer_id = customer_id
    state.active_customer_id = customer_id


def persist_active_customer(state: CustomerServiceState) -> None:
    if state.active_customer_id:
        state.customer_contexts[state.active_customer_id] = _snapshot(state)


def summaries_for_members(state: CustomerServiceState, builder) -> dict[str, dict[str, Any]]:
    current = state.active_customer_id
    persist_active_customer(state)
    result = {}
    for customer_id in state.group_member_ids or [state.customer_id]:
        if customer_id:
            activate_customer(state, customer_id)
            result[customer_id] = builder(state)
    if current:
        activate_customer(state, current)
    return result
