from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any

from backend.app.db.seed import load_products_from_seed, seed_inventory
from backend.app.domain.business_config import load_persisted, snapshot
from backend.app.domain.catalog import PRODUCTS
from backend.app.domain.pricing_service import calculate_order_quote


def bootstrap_fixture() -> dict[str, Any]:
    load_products_from_seed()
    seed_inventory()
    load_persisted()
    fixture = deepcopy(snapshot())
    fixture.pop("inventory", None)
    encoded = repr(fixture).encode("utf-8")
    fixture["fixture_version"] = sha256(encoded).hexdigest()[:12]
    fixture["product_count"] = len(PRODUCTS)
    return fixture


def product_by_name(name: str) -> dict[str, Any] | None:
    return next((item for item in PRODUCTS if item["name"] == name), None)


def expected_quote(entities: list[dict[str, Any]], customer_type: str = "REGULAR") -> dict[str, Any]:
    items = []
    for entity in entities:
        product = product_by_name(entity["product_name"])
        if not product:
            return {"ok": False, "reason": "FIXTURE_PRODUCT_NOT_FOUND"}
        items.append({"product_id": product["id"], "quantity": entity["quantity"]})
    return calculate_order_quote(items, customer_type=customer_type)


def trace_tools(traces: list[dict[str, Any]]) -> list[str]:
    return [
        trace.get("next_action", {}).get("tool_name")
        for trace in traces
        if trace.get("next_action", {}).get("tool_name")
    ]


def assert_followup_recovery(state: Any, trace: dict[str, Any], reply: str) -> dict[str, Any]:
    """Deterministic assertions for an accepted assistant proposal."""
    action = trace.get("next_action", {})
    constraints = state.known_facts.get("recommendation_constraints", {}).get("constraints", {})
    return {
        "followup_recovered": action.get("tool_name") == "recommend_products",
        "child_constraint_retained": constraints.get("audience") in {"儿童", "CHILD"},
        "premature_handoff": trace.get("status") == "HANDOFF" or "转人工" in reply,
        "internal_fields_exposed": any(value in reply for value in ("SKU", "recommendation_constraints", "tool_name")),
    }


def clarification_summary(states: list[Any], traces: list[dict[str, Any]]) -> dict[str, Any]:
    acts = [getattr(state, "conversation_act", "REQUEST") for state in states]
    missing = [slot.get("name") for state in states for slot in getattr(state, "missing_slots", [])]
    blocked_side_effects = sum(
        1 for trace in traces
        if trace.get("reason_code") in {"DELIVERY_SLOT_REQUIRED", "DELIVERY_CONFIRMATION_REQUIRED"}
        and trace.get("next_action", {}).get("tool_name") in {"create_delivery_request", "submit_delivery_request", "create_order"}
    )
    return {
        "conversation_acts": acts,
        "missing_slots": list(dict.fromkeys(missing)),
        "clarification_count": sum(1 for trace in traces if trace.get("next_action", {}).get("type") == "ASK_USER"),
        "blocked_side_effect_count": blocked_side_effects,
        "selection_detected": "SELECT" in acts or "ADD" in acts,
    }


def _actual_products(state) -> list[dict[str, Any]]:
    resolved = state.known_facts.get("resolved_products", [])
    selected = state.known_facts.get("selected_products", [])
    return resolved if resolved else selected


def score_case(case: dict[str, Any], states: list[Any], traces: list[dict[str, Any]], replies: list[str], fixture: dict[str, Any]) -> dict[str, Any]:
    expected = case["expected"]
    state = states[-1]
    tools = trace_tools(traces)
    actual_goals = {item.get("type") for item in state.goals}
    actual_goals.update(trace.get("goal", {}).get("type") for trace in traces)
    actual_goals.discard(None)
    goal_score = int(set(expected.get("goals", [])) & actual_goals == set(expected.get("goals", [])))

    actual_entities = next((_actual_products(candidate) for candidate in reversed(states) if _actual_products(candidate)), [])
    entity_score = 1
    for expected_item in expected.get("entities", []):
        match = next((item for item in actual_entities if item.get("name") == expected_item["product_name"] or item.get("product_name") == expected_item["product_name"]), None)
        if not match or int(match.get("quantity", 1)) != expected_item["quantity"]:
            entity_score = 0
            break

    # State correctness is evaluated independently from the final prose. This
    # catches a stale quote even when the reply happens to contain a plausible
    # number.
    expected_state = {
        item["product_name"]: int(item["quantity"])
        for item in expected.get("entities", [])
    }
    actual_state = {
        item.get("name") or item.get("product_name"): int(item.get("quantity", 1))
        for item in state.known_facts.get("selected_products", [])
        if item.get("name") or item.get("product_name")
    }
    state_mutation_score = int(bool(expected_state) and all(actual_state.get(name) == quantity for name, quantity in expected_state.items())) if expected_state else 1

    required = set(expected.get("required_capabilities", []))
    forbidden = set(expected.get("forbidden_tools", []))
    tool_score = int(required.issubset(set(tools)) and not forbidden.intersection(tools)) if required else int(not forbidden.intersection(tools))
    business_score = 0
    business_detail: dict[str, Any] = {}
    result_type = expected.get("result_type")
    if result_type == "QUOTE":
        quote = state.quote_context.model_dump() if state.quote_context else state.known_facts.get("quote_context", {})
        expected_result = expected_quote(expected.get("entities", []))
        actual_subtotal = quote.get("subtotal")
        actual_total = quote.get("total") or quote.get("last_quote_total")
        expected_data = expected_result.get("data", {}) if expected_result.get("ok") else {}
        expected_subtotal = expected_data.get("subtotal")
        expected_total = expected_data.get("total")
        business_score = int(actual_subtotal is not None and expected_subtotal is not None and float(actual_subtotal) == float(expected_subtotal))
        business_detail = {"expected_subtotal": expected_subtotal, "actual_subtotal": actual_subtotal, "expected_total": expected_total, "actual_total": actual_total}
    elif result_type == "BROWSE":
        available = state.known_facts.get("available_products", [])
        business_score = int(bool(available) and all(item.get("category") == expected.get("category") or expected.get("category") in item.get("name", "") for item in available))
        business_detail = {"available_products": [item.get("name") for item in available]}
    elif result_type == "INVENTORY":
        business_score = int(any(result.get("ok") for result in state.tool_results))
    elif result_type == "RECOMMENDATION":
        candidates = state.known_facts.get("recommendations", [])
        rule = expected.get("recommendation", {})
        total = sum(float(item.get("price", 0)) for item in candidates)
        categories = [item.get("category") for item in candidates]
        business_score = int(
            len(candidates) == rule.get("count")
            and len({item.get("id") for item in candidates}) == len(candidates)
            and all((item.get("available_quantity") or 0) > 0 for item in candidates)
            and ("max_total" not in rule or total <= rule["max_total"])
            and ("categories" not in rule or all(category in categories for category in rule["categories"]))
        )
        business_detail = {"recommendations": candidates, "total": total}
    elif result_type == "COMPARE":
        compared = state.known_facts.get("comparison", {})
        business_score = int(bool(compared.get("cheapest")))
        business_detail = compared
    elif result_type == "POLICY":
        business_score = int(bool(state.known_facts.get("quote_context") or state.known_facts.get("sales_policy") or state.known_facts.get("promotion")))
    elif result_type == "RESERVATION":
        expected_status = expected.get("reservation_status", "RESERVED")
        reservations = state.known_facts.get("reservations", [])
        business_score = int((expected_status == "RESERVED" and any(item.get("status") == "RESERVED" and item.get("quantity") == expected.get("quantity", 1) for item in reservations)) or (expected_status == "REJECTED" and not reservations and any("库存" in reply or "可售" in reply for reply in replies)))
        business_detail = {"reservations": reservations, "expected_status": expected_status}
    elif result_type == "CLARIFICATION":
        last_action = traces[-1].get("next_action", {}) if traces else {}
        business_score = int(last_action.get("type") == "ASK_USER" and traces[-1].get("reason_code") == "AMBIGUOUS_REFERENCE")
    elif case.get("category") == "STORE_SERVICE":
        topic = expected.get("topic", "")
        business_score = int(any(topic in reply for reply in replies))
    elif case.get("category") == "RECOMMENDATION":
        candidates = state.known_facts.get("recommendations", [])
        business_score = int(bool(candidates) and all((item.get("available_quantity") or 0) > 0 for item in candidates))
    response_text = replies[-1] if replies else ""
    forbidden_text = expected.get("must_not_expose", [])
    response_score = int(bool(response_text.strip()) and "LLM_OUTPUT_INVALID" not in response_text and not response_text.strip().startswith("{") and not any(value in response_text for value in forbidden_text))
    if forbidden.intersection(tools):
        response_score = 0
    return {
        "id": case["id"], "turns": case["turns"], "replies": replies, "traces": traces,
        "state_mutation_score": state_mutation_score,
        "scores": {"goal": goal_score, "entity": entity_score, "tool": tool_score, "business_result": business_score, "response_safety": response_score},
        "total": goal_score + entity_score + tool_score + business_score + response_score,
        "tools": tools, "business_detail": business_detail,
        "clarification": clarification_summary(states, traces),
        "fixture_version": fixture["fixture_version"],
    }
