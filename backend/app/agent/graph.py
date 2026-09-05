import os
from typing import Any, TypedDict

from .contracts import Goal, NextAction, PlannerOutput, PendingFollowup, UnderstandingOutput, ResponseContext
from .capability_resolver import resolve_capabilities
from .goal_stack import infer_goal_types, transition_goals, update_goal_status
from .planner import plan
from .plan_validator import validate_plan
from .recommendation_renderer import render as render_recommendations
from .state import CustomerServiceState
from ..domain.handoff_service import create_handoff
from ..tools.registry import execute
from ..domain.catalog import PRODUCTS
from ..domain.recommendation_service import normalize_constraints, relaxation_options
from ..domain.media_service import list_media
from ..trace_service import begin_run, finish_run, record
from .understanding import understand, resolve_products
from .supervisor import SupervisorAgent
from .commerce_agent import CommerceAgent
from ..trace_service import record_agent_task, record_agent_transition
from .feedback import detect_feedback
from .semantic_state import merge_understanding_state, semantic_from_constraints
from .turn_evaluator import evaluate_turn
from ..domain.memory_service import read as read_memory, write as write_memory
from .reference_resolver import resolve_reference
from .semantic_workspace import understand_semantic, semantic_action, to_understanding
from .followup_resolver import resolve_followup
from .policy_gate import decide as policy_decide
from .response_composer import compose as compose_response


def _state_snapshot(state: CustomerServiceState) -> dict[str, Any]:
    return {
        "semantic_state": state.semantic_state,
        "goals": state.goals,
        "selected_products": state.known_facts.get("selected_products", []),
        "focused_product": state.focused_product,
        "recent_products": state.recent_products,
        "quote_context": state.quote_context.model_dump() if state.quote_context else None,
        "status": state.status,
        "conversation_act": state.conversation_act,
        "missing_slots": state.missing_slots,
        "recommendation_candidates": state.recommendation_candidates,
        "reference_context": state.reference_context,
        "delivery_slots": {key: "<redacted>" if key in {"phone", "delivery_address"} else value for key, value in state.delivery_slots.items()},
        "delivery_mode": state.delivery_mode,
        "pending_followup": state.pending_followup.model_dump() if state.pending_followup else None,
    }


def _lineage(state: CustomerServiceState, component: str, before: dict[str, Any], output: dict[str, Any], started: float, status: str = "PASS", error_code: str | None = None) -> None:
    import time
    record(state.session_id, {
        "step_type": "lineage", "turn_id": f"{state.session_id}:{state.turn_count}",
        "lineage": {"component": component, "input": before, "output": output,
                     "before_state": before, "after_state": _state_snapshot(state),
                     "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                     "status": status, "error_code": error_code},
    }, state.known_facts.get("run_id"))


class TurnGraphState(TypedDict, total=False):
    state: CustomerServiceState | dict
    text: str
    confirmed: bool
    run_id: str
    output: PlannerOutput
    result: Any
    reply: str
    trace: dict
    handoff_reason: str
    direct_action: bool
    capabilities: list[str]
    supervisor_decision: Any
    short_path: bool


def _load_context(ctx: TurnGraphState) -> dict:
    state = CustomerServiceState.model_validate(ctx["state"])
    state.turn_count += 1
    state.original_request = state.original_request or ctx["text"]
    state.add_message("user", ctx["text"], state.active_customer_id)
    state.known_facts["response_attachments"] = []
    state.known_facts.pop("preserve_selection", None)
    state.known_facts["confirmed_memory"] = read_memory(state.customer_id)
    run_id = begin_run(state.session_id)
    state.known_facts["run_id"] = run_id
    return {"state": state, "run_id": run_id}


def _understand(ctx: TurnGraphState) -> dict:
    state = ctx["state"]
    import time
    started = time.perf_counter()
    before = _state_snapshot(state)
    state.known_facts["last_user_message"] = ctx["text"]
    try:
        followup = resolve_followup(ctx["text"], state.pending_followup)
        if followup.type != "NONE":
            state.known_facts["followup_intent"] = followup.model_dump()
            _lineage(state, "FOLLOWUP_INTENT_RESOLVER", before, followup.model_dump(), started)
            if followup.type == "ACCEPT_FOLLOWUP" and state.pending_followup:
                pending = state.pending_followup
                semantic = UnderstandingOutput(
                    goals=["PRODUCT_RECOMMENDATION"] if pending.type == "RECOMMEND_PRODUCTS" else [],
                    constraints=pending.constraints,
                    conversation_act="FOLLOW_UP",
                    semantic_state={"how": pending.constraints},
                )
                state.known_facts["understanding"] = semantic.model_dump()
                state.known_facts["resolved_products"] = []
                state.known_facts["reference_resolution"] = {}
                state.known_facts["understanding_status"] = "VALID"
                state.known_facts["pending_followup_accepted"] = True
                state.pending_followup_history.append({**pending.model_dump(), "result": followup.type})
                state.pending_followup = None
                return {"state": state}
            if followup.type == "REJECT_FOLLOWUP":
                state.pending_followup_history.append({**state.pending_followup.model_dump(), "result": followup.type})
                state.pending_followup = None
        if __import__("os").getenv("AGENT_ARCHITECTURE", "legacy").lower() in {"semantic", "converged"}:
            workspace = understand_semantic(state, ctx["text"])
            state.known_facts["semantic_workspace"] = workspace.model_dump()
            state.known_facts["semantic_action"] = semantic_action(workspace)
            semantic = to_understanding(workspace)
            # The workspace supplies language targets only. The existing
            # Resolver remains the sole SKU authority; delivery extraction is
            # limited to explicit current-turn values.
            from .understanding import _delivery_slot_values
            semantic.slot_values = _delivery_slot_values(ctx["text"])
            semantic.delivery_intent = any(word in ctx["text"] for word in ("邮寄", "寄送", "配送", "顺丰"))
            semantic.delivery_mode = "PICKUP" if any(word in ctx["text"] for word in ("到店取", "自取")) else "SHIPPING" if semantic.delivery_intent else "UNKNOWN"
        else:
            semantic = understand(state, ctx["text"])
        state.known_facts["understanding"] = semantic.model_dump()
        if semantic.memory_candidate and state.customer_id:
            memory_result = write_memory(state.customer_id, semantic.memory_candidate)
            state.known_facts["memory_write_result"] = memory_result
            _lineage(state, "MEMORY_CANDIDATE", before, {"candidate": semantic.memory_candidate}, started)
            _lineage(state, "MEMORY_POLICY", before, memory_result, started, "PASS" if memory_result.get("ok") else "FAIL", memory_result.get("reason"))
        resolved_products = resolve_products(semantic)
        candidate_ids = set(state.recommendation_candidates or state.known_facts.get("recommendation_context", {}).get("previous_product_ids", []))
        candidate_names = {item.get("name") for item in state.known_facts.get("recommendations", [])}
        has_previous_recommendation = bool(
            state.known_facts.get("recommendation_context")
            or state.known_facts.get("recommendations")
        )
        for item in resolved_products:
            if (
                item.get("product_id") in candidate_ids
                or item.get("name") in candidate_names
                or item.get("query") in candidate_names
                or has_previous_recommendation
            ):
                item["reference_source"] = "previous_recommendation_candidates"
        state.known_facts["resolved_products"] = resolved_products
        reference = resolve_reference(state, resolved_products)
        state.known_facts["reference_resolution"] = reference
        if len(resolved_products) == 1 and resolved_products[0].get("product_id"):
            state.focused_product = dict(resolved_products[0])
            state.recent_products = [state.focused_product] + [item for item in state.recent_products if item.get("product_id") != state.focused_product.get("product_id")]
        elif len(resolved_products) > 1:
            state.focused_product = None
            state.recent_products = [dict(item) for item in resolved_products if item.get("product_id")]
        state.known_facts["understanding_status"] = "VALID"
        previous_semantic = state.semantic_state
        llm_semantic = semantic.semantic_state or semantic_from_constraints(semantic.constraints)
        state.semantic_state = merge_understanding_state(previous_semantic, llm_semantic, semantic.constraint_updates)
        feedback = semantic.feedback or detect_feedback(ctx["text"], state.known_facts.get("previous_understanding"))
        if feedback:
            state.feedback_events.append(feedback)
            state.known_facts["feedback"] = feedback
        state.known_facts["previous_understanding"] = semantic.model_dump()
        _lineage(state, "UNDERSTANDING", before, semantic.model_dump(), started)
        _lineage(state, "NORMALIZATION", before, {"semantic_state": state.semantic_state}, started)
        _lineage(state, "ENTITY_RESOLVER", before, {"resolved_products": state.known_facts["resolved_products"]}, started)
        _lineage(state, "CONSTRAINT_EXTRACTION", before, {"constraints": semantic.constraints, "updates": semantic.constraint_updates}, started)
    except Exception as exc:
        state.known_facts["understanding_status"] = "FAILED"
        state.known_facts["understanding_error"] = {"stage": "understanding", "error_type": type(exc).__name__}
        record(state.session_id, {"step_type": "understanding_error", "stage": "understanding", "error_type": type(exc).__name__}, ctx["run_id"])
        _lineage(state, "UNDERSTANDING", before, {}, started, "FAIL", type(exc).__name__)
    return {"state": state}


def _apply_converged_mutation(ctx: TurnGraphState) -> dict:
    state = ctx["state"]
    if os.getenv("AGENT_ARCHITECTURE", "legacy").lower() not in {"converged", "semantic"}:
        return {"state": state}
    action = state.known_facts.get("semantic_action", {})
    operation = action.get("operation")
    if operation not in {"SELECT", "ADD", "REMOVE", "SET_QUANTITY", "REPLACE", "KEEP"}:
        return {"state": state}
    # Inventory/product lookup discusses a product but does not select it.
    # Only selection-oriented intents may promote an item into the working set.
    if action.get("intent") in {"INVENTORY_CHECK", "PRODUCT_BROWSE", "PRODUCT_RECOMMENDATION"} and operation in {"SELECT", "ADD"}:
        return {"state": state}
    from .reference_resolver import resolve_semantic_target
    from .state_mutation import apply_action
    reference = resolve_semantic_target(state, action.get("target"))
    state.known_facts["reference_resolution"] = reference
    mutation = apply_action(state, operation, reference, action.get("quantity"))
    state.known_facts["state_mutation"] = mutation
    _lineage(state, "STATE_UPDATER", _state_snapshot(state), mutation, __import__("time").perf_counter(), "PASS" if mutation["status"] == "PASS" else "FAIL", None if mutation["status"] == "PASS" else mutation["status"])
    return {"state": state}


def _update_goal_stack(ctx: TurnGraphState) -> dict:
    state = ctx["state"]
    import time
    started = time.perf_counter()
    before = _state_snapshot(state)
    understanding = state.known_facts.get("understanding", {})
    semantic_goals = understanding.get("goals") or understanding.get("candidate_goals") or infer_goal_types(ctx["text"])
    operations = understanding.get("requested_items", [])
    has_selection_operation = any(item.get("operation") in {"ADD", "REMOVE", "SET_QUANTITY", "REPLACE"} for item in operations)
    answers_quantity = any(char.isdigit() for char in ctx["text"]) or any(word in ctx["text"] for word in ("一个", "两个", "三个", "四个"))
    if state.known_facts.get("pending_selection") and state.missing_slots and answers_quantity:
        semantic_goals = ["PRICE_CALCULATION"]
    if state.known_facts.get("selected_products") and (has_selection_operation or any(word in ctx["text"] for word in ("再加", "增加", "改成", "换成"))):
        semantic_goals = ["PRICE_CALCULATION"]
    transitions = transition_goals(state, semantic_goals)
    state.known_facts["last_goal_transition"] = transitions[-1] if transitions else None
    _lineage(state, "GOAL_MANAGER", before, {"goals": state.goals, "transition": state.known_facts["last_goal_transition"]}, started)
    return {"state": state}


def _supervise(ctx: TurnGraphState) -> dict:
    state = ctx["state"]
    if state.known_facts.get("understanding_status") != "VALID":
        return {"state": state}
    from .contracts import UnderstandingOutput
    understanding = UnderstandingOutput.model_validate(state.known_facts.get("understanding", {}))
    if os.getenv("AGENT_ARCHITECTURE", "legacy").lower() in {"converged", "semantic"}:
        decision = SupervisorAgent().decide_domain(understanding, ctx["text"])
        state.known_facts["supervisor_domain_decision"] = decision.model_dump()
        state.active_domain = decision.domain
        state.active_agent = decision.domain if decision.domain in {"COMMERCE", "AFTER_SALES"} else "SUPERVISOR"
        if decision.reason_code == "HUMAN_HANDOFF":
            from .contracts import HandoffState
            state.execution_mode = "HUMAN_HANDOFF"
            state.handoff_state = HandoffState(reason_code=decision.reason_code, context={"user_text": ctx["text"]})
            state.requires_human = True
            state.status = "HANDOFF"
        record_agent_transition(
            state.session_id,
            {"from": "SUPERVISOR", "domain": state.active_domain, "execution_mode": state.execution_mode, "reason_code": decision.reason_code},
            ctx["run_id"],
        )
        return {"state": state, "supervisor_domain_decision": decision}
    decision = SupervisorAgent().decide(understanding, ctx["text"])
    state.known_facts["supervisor_decision"] = decision.model_dump()
    state.task_stack = [task.model_dump() for task in decision.tasks]
    if decision.domain in {"COMMERCE", "AFTER_SALES"}:
        state.active_agent = decision.domain
    record_agent_transition(
        state.session_id,
        {"from_agent": "SUPERVISOR", "to_agent": state.active_agent, "route_action": decision.route_action, "reason_code": decision.reason_code},
        ctx["run_id"],
    )
    for task in decision.tasks:
        record_agent_task(state.session_id, task.model_dump(), ctx["run_id"])
    return {"state": state, "supervisor_decision": decision}


def _resolve_capabilities(ctx: TurnGraphState) -> dict:
    state = ctx["state"]
    active = [goal for goal in state.goals if goal["status"] == "ACTIVE"]
    # Include goals detected in the current turn. A delivery-mode correction
    # can legitimately transition a prior recommendation/selection flow into
    # a quote recalculation before the goal stack is persisted.
    current = state.known_facts.get("understanding", {}).get("goals", [])
    capabilities = sorted({tool for goal in active + [{"type": goal} for goal in current] for tool in resolve_capabilities(goal["type"])})
    if state.known_facts.get("pending_reservation"):
        capabilities = sorted(set(capabilities) | set(resolve_capabilities("RESERVATION")))
    if state.quote_context and state.known_facts.get("understanding", {}).get("delivery_mode") in {"PICKUP", "SHIPPING"}:
        capabilities = sorted(set(capabilities) | set(resolve_capabilities("PRICE_CALCULATION")))
    state.known_facts["capabilities"] = capabilities
    _lineage(state, "CAPABILITY_RESOLVER", _state_snapshot(state), {"capabilities": capabilities}, __import__("time").perf_counter())
    return {"state": state, "capabilities": capabilities}


def _converged_atomic_output(state: CustomerServiceState, text: str) -> PlannerOutput | None:
    """Map simple read-only actions without invoking the complex Planner."""
    if os.getenv("AGENT_ARCHITECTURE", "legacy").lower() not in {"converged", "semantic"}:
        return None
    understanding = state.known_facts.get("understanding", {})
    goals = set(understanding.get("goals", []))
    resolved = [item for item in state.known_facts.get("resolved_products", []) if item.get("product_id")]
    if "INVENTORY_CHECK" in goals and len(resolved) == 1:
        return PlannerOutput(
            goal=Goal(type="INVENTORY_CHECK"),
            next_action=NextAction(type="TOOL_CALL", tool_name="check_inventory", arguments={"product_id": resolved[0]["product_id"]}),
            reason_code="ATOMIC_INVENTORY_QUERY",
            current_goal_id=None,
        )
    if "PRODUCT_BROWSE" in goals:
        category = next((item.get("category") for item in resolved if item.get("category")), None)
        if category is None:
            # Category extraction is normalization, not a planner/tool rule;
            # use the catalog vocabulary so “有什么贝果” reaches the domain
            # inventory query with a complete argument.
            category = next((value for value in {item.get("category") for item in PRODUCTS} if value and value in text), None)
            if category is None:
                category = next((value for value in {item.get("name") for item in PRODUCTS} if value and value in text), None)
        return PlannerOutput(
            goal=Goal(type="PRODUCT_BROWSE"),
            next_action=NextAction(type="TOOL_CALL", tool_name="list_available_inventory", arguments={"category": category, "query": ""}),
            reason_code="ATOMIC_PRODUCT_BROWSE",
            current_goal_id=None,
        )
    if "PRODUCT_COMPARE" in goals:
        candidate_ids = list(state.recommendation_candidates)
        if not candidate_ids:
            candidate_ids = [item.get("id") or item.get("product_id") for item in state.known_facts.get("recommendations", [])]
        if candidate_ids:
            return PlannerOutput(
                goal=Goal(type="PRODUCT_COMPARE"),
                next_action=NextAction(type="TOOL_CALL", tool_name="compare_products", arguments={"product_ids": candidate_ids}),
                reason_code="ATOMIC_PRODUCT_COMPARE",
                current_goal_id=None,
            )
    if "PRICE_CALCULATION" in goals:
        items = state.known_facts.get("selected_products", []) if state.known_facts.get("state_mutation", {}).get("status") == "PASS" else state.quote_context.items if state.quote_context and state.quote_context.items else state.known_facts.get("selected_products", [])
        if items and not any(item.get("operation") in {"REMOVE", "SET_QUANTITY", "REPLACE"} for item in resolved):
            return PlannerOutput(
                goal=Goal(type="PRICE_CALCULATION"),
                next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}),
                reason_code="ATOMIC_QUOTE_QUERY",
                current_goal_id=None,
            )
    return None


def _planner(ctx: TurnGraphState) -> dict:
    state = ctx["state"]
    if state.execution_mode == "HUMAN_HANDOFF":
        output = PlannerOutput(
            goal=Goal(type="OTHER", status="BLOCKED"),
            next_action=NextAction(type="HANDOFF", message="已为你转接人工客服，并保留当前对话。"),
            reason_code="HUMAN_HANDOFF",
            current_goal_id=None,
        )
        return {"state": state, "output": output}
    if (
        os.getenv("AGENT_ARCHITECTURE", "legacy").lower() not in {"converged", "semantic"}
        and ctx.get("confirmed")
        and state.known_facts.get("order_id")
    ):
        result = execute(
            "create_return_request",
            {
                "order_id": state.known_facts["order_id"],
                "customer_id": state.customer_id or "CUS001",
                "confirmed": True,
            },
        )
        trace = {"step_type": "tool_call", "tool_name": "create_return_request", "result": result.model_dump()}
        record(state.session_id, trace, ctx["run_id"])
        state.completed_steps.append("create_return_request")
        state.status = "RESOLVED" if result.ok else "HANDOFF"
        reply = "退货申请已提交，申请编号为 " + result.data["id"] if result.ok else "提交失败，请转人工处理。"
        return {"state": state, "result": result, "reply": reply, "trace": trace, "direct_action": True}

    output = _converged_atomic_output(state, ctx["text"])
    if output is None:
        output = CommerceAgent().plan_turn(state, ctx["text"], ctx.get("capabilities", [])) if state.active_agent == "COMMERCE" else plan(state, ctx["text"], ctx.get("capabilities", []))
    state.pending_items = output.missing_information
    record(
        state.session_id,
        {"step_type": "planner", "reason_code": output.reason_code, "action": output.next_action.model_dump()},
        ctx["run_id"],
    )
    state.completed_steps.append(f"planner:{output.reason_code}")
    _lineage(state, "PLANNER", _state_snapshot(state), {"output": output.model_dump()}, __import__("time").perf_counter())
    return {"state": state, "output": output}


def _select_converged_path(ctx: TurnGraphState) -> dict:
    """Select the atomic path before Supervisor/Goal Manager in Converged Mode."""
    state = ctx["state"]
    output = _converged_atomic_output(state, ctx["text"])
    if output is None:
        return {"state": state, "short_path": False}
    _lineage(
        state,
        "SUPERVISOR_ROUTER",
        _state_snapshot(state),
        {"route": "ATOMIC_SHORT_PATH", "action": output.next_action.model_dump()},
        __import__("time").perf_counter(),
    )
    return {"state": state, "output": output, "short_path": True}


def _converged_short_path(ctx: TurnGraphState) -> dict:
    """Pass an already-selected atomic decision to the common executor route."""
    return {"state": ctx["state"], "output": ctx["output"]}


def _route_after_path_selection(ctx: TurnGraphState) -> str:
    return "short_path" if ctx.get("short_path") else "supervisor"


def _validate(ctx: TurnGraphState) -> dict:
    if ctx.get("direct_action"):
        return {}
    output = ctx["output"]
    state = ctx["state"]
    # “还是一个/还是两个” is a confirmation of the existing working set,
    # never a request to mutate the first item by fallback heuristics.
    if state.known_facts.get("selected_products") and "还是" in ctx["text"] and state.quote_context and state.quote_context.items:
        output = PlannerOutput(
            goal=Goal(type="PRICE_CALCULATION"),
            next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": state.quote_context.items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}),
            reason_code="SELECTION_CONFIRMED_UNCHANGED",
            current_goal_id=None,
        )
    # A follow-up quote/policy question must reuse the current quote unless the
    # current turn contains a new resolved product operation.
    if output.next_action.type == "TOOL_CALL" and output.next_action.tool_name == "calculate_order_quote":
        resolved = state.known_facts.get("resolved_products", [])
        if state.quote_context and not resolved:
            arguments = dict(output.next_action.arguments)
            arguments["items"] = state.quote_context.items
            output = PlannerOutput(
                goal=output.goal,
                next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments=arguments),
                reason_code=output.reason_code,
                missing_information=output.missing_information,
                requires_confirmation=output.requires_confirmation,
                current_goal_id=output.current_goal_id,
                decision_summary=output.decision_summary,
            )
    capabilities = list(ctx.get("capabilities", []))
    # A category-only browse is a safe, read-only action even when the LLM
    # understanding is empty. The deterministic planner has already supplied
    # a validated category; make the matching capability available instead of
    # converting a recoverable provider miss into a handoff.
    if (
        output.next_action.type == "TOOL_CALL"
        and output.next_action.tool_name == "list_available_inventory"
        and output.next_action.arguments.get("category")
    ):
        capabilities.append("list_available_inventory")
        capabilities = sorted(set(capabilities))
    converged = os.getenv("AGENT_ARCHITECTURE", "legacy").lower() in {"converged", "semantic"}
    if converged:
        from .action_planner import to_execution_decision
        from .plan_validator import validate_execution_decision
        try:
            validate_execution_decision(to_execution_decision(output), set(capabilities))
            validated = output
        except ValueError:
            validated = PlannerOutput(
                goal=Goal(type=output.goal.type, status="BLOCKED"),
                next_action=NextAction(type="HANDOFF", message="当前请求无法安全执行，我为你转人工处理。"),
                reason_code="CAPABILITY_NOT_ALLOWED",
                current_goal_id=output.current_goal_id,
            )
    else:
        validated = validate_plan(output, capabilities)
    if state.known_facts.get("preserve_selection") and output.next_action.tool_name == "calculate_order_quote":
        # This is a validated, read-only re-quote over the existing state;
        # do not let an unrelated stale capability list trigger handoff.
        validated = output
    if validated.reason_code == "CAPABILITY_NOT_ALLOWED" and not state.known_facts.get("preserve_selection") and state.known_facts.get("replan_count", 0) < 1:
        understanding = state.known_facts.get("understanding", {})
        goals = understanding.get("goals", [])
        recovered = None
        # A quantity-only turn is a state mutation even when the model emits
        # an invalid goal/tool combination. Recover against the focused or
        # uniquely selected product before considering human handoff.
        if any(char.isdigit() for char in ctx["text"]) or any(word in ctx["text"] for word in ("一个", "两个", "三个", "改成", "再来")):
            from .reference_resolver import reference_product
            reference = state.known_facts.get("reference_resolution", {})
            item = reference_product(state, reference)
            selected = [dict(item)] if item else [dict(value) for value in state.known_facts.get("selected_products", [])]
            if selected:
                import re
                match = re.search(r"(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个", ctx["text"])
                numbers = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
                quantity = int(match.group(1)) if match and match.group(1).isdigit() else numbers.get(match.group(1), 1) if match else 1
                selected[0]["quantity"] = quantity
                state.known_facts["selected_products"] = selected
                recovered = PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": selected, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="CAPABILITY_RECOVERED_STATE_MUTATION", current_goal_id=None)
        if recovered is None and "PRODUCT_COMPARE" in goals:
            resolved = [item for item in state.known_facts.get("resolved_products", []) if item.get("product_id")]
            category = next((value for value in ("贝果", "吐司", "欧包", "盐面包") if value in ctx["text"]), None)
            recovered = PlannerOutput(goal=Goal(type="PRODUCT_COMPARE"), next_action=NextAction(type="TOOL_CALL", tool_name="compare_products", arguments={"product_ids": [item["product_id"] for item in resolved], "category": category}), reason_code="REPLAN_AFTER_INVALID_PLAN", current_goal_id=None)
        elif "PRODUCT_FIT_QUERY" in goals:
            resolved = next((item for item in state.known_facts.get("resolved_products", []) if item.get("product_id")), None)
            if resolved:
                constraints = understanding.get("constraints", {})
                recovered = PlannerOutput(goal=Goal(type="PRODUCT_FIT_QUERY"), next_action=NextAction(type="TOOL_CALL", tool_name="explain_product_fit", arguments={"product_id": resolved["product_id"], "audience": constraints.get("audience"), "concern": constraints.get("concern", "audience")}), reason_code="REPLAN_AFTER_INVALID_PLAN", current_goal_id=None)
        if recovered:
            state.known_facts["replan_count"] = state.known_facts.get("replan_count", 0) + 1
            validated = validate_plan(recovered, list(set(capabilities) | set(resolve_capabilities(recovered.goal.type))))
    _lineage(state, "PLAN_VALIDATOR", _state_snapshot(state), {"output": validated.model_dump()}, __import__("time").perf_counter(), "FAIL" if validated.reason_code == "CAPABILITY_NOT_ALLOWED" else "PASS", validated.reason_code if validated.reason_code == "CAPABILITY_NOT_ALLOWED" else None)
    return {"output": validated}


def _policy_gate(ctx: TurnGraphState) -> dict:
    if ctx.get("direct_action"):
        return {}
    output = ctx["output"]
    policy = policy_decide(output.next_action.tool_name, confirmed=ctx.get("confirmed", False))
    if policy.decision == "REQUIRE_CONFIRMATION" and output.next_action.type == "TOOL_CALL":
        output = PlannerOutput(
            goal=output.goal,
            next_action=NextAction(type="ASK_CONFIRMATION", message="执行该操作前需要你的明确确认。"),
            reason_code="CONFIRMATION_REQUIRED",
            requires_confirmation=True,
            current_goal_id=output.current_goal_id,
        )
    if output.next_action.type == "TOOL_CALL" and output.next_action.tool_name == "create_return_request" and not ctx.get("confirmed"):
        output = PlannerOutput(
            goal=output.goal,
            next_action=NextAction(type="ASK_CONFIRMATION", message="执行退货申请前需要你的明确确认。"),
            reason_code="CONFIRMATION_REQUIRED",
            requires_confirmation=True,
            current_goal_id=output.current_goal_id,
        )
    return {"output": output}


def _route(ctx: TurnGraphState) -> dict:
    if ctx.get("direct_action"):
        return {}
    state = ctx["state"]
    output = ctx["output"]
    action = output.next_action
    trace = {"goal": output.goal.model_dump(), "next_action": action.model_dump(), "reason_code": output.reason_code}
    if action.type == "TOOL_CALL":
        if os.getenv("AGENT_ARCHITECTURE", "legacy").lower() in {"converged", "semantic"}:
            from .action_planner import to_execution_decision
            from .executor import ActionExecutor
            result = ActionExecutor().execute(to_execution_decision(output))
        else:
            result = execute(action.tool_name, action.arguments)
        record(
            state.session_id,
            {"step_type": "tool_call", "tool_name": action.tool_name, "arguments": action.arguments, "result": result.model_dump()},
            ctx["run_id"],
        )
        state.completed_steps.append(action.tool_name)
        state.tool_results.append(result.model_dump())
        if action.tool_name == "find_recent_orders" and result.ok and result.data:
            state.known_facts["order_id"] = result.data[0]["id"]
            reply = f"我找到订单 {result.data[0]['id']}，商品是{result.data[0]['item_name']}。我继续确认退货资格。"
        elif action.tool_name == "check_return_eligibility" and result.ok and result.data.get("eligible"):
            state.known_facts["eligibility"] = True
            state.requires_confirmation = True
            state.status = "WAITING_CONFIRMATION"
            reply = "订单符合当前退货规则。是否确认提交退货申请？"
        elif action.tool_name == "check_inventory" and result.ok:
            data = result.data
            product = next((item for item in PRODUCTS if item["id"] == data["product_id"]), None)
            if product:
                state.known_facts["response_attachments"] = [
                    {"type": "image", "url": f"/api/v1/media/{media['media_id']}", "alt": media.get("alt", product["name"])}
                    for media in list_media(product_id=product["id"])
                ]
                state.focused_product = {"product_id": product["id"], "name": product["name"], "quantity": 1, "unit_price": product["price"], "selection_status": "FOCUSED", "source": "inventory_lookup"}
                state.recent_products = [state.focused_product] + [item for item in state.recent_products if item.get("product_id") != product["id"]]
            if data.get("inventory_status") == "UNKNOWN":
                reply = f"暂时无法确认{data['name']}的实时库存，建议转人工处理。"
            else:
                reply = f"{data['name']}目前{'有货' if data['available'] else '缺货'}，可售库存 {data['available_quantity']} 件，查询时间为 {result.observed_at}。"
        elif action.tool_name == "list_available_inventory" and result.ok:
            items = result.data or []
            state.known_facts["available_products"] = items
            # Browse results remain referenceable candidates, but are not a
            # purchase selection. This enables later “第二个/最便宜的” turns.
            state.recommendation_candidates = [item.get("product_id") or item.get("id") for item in items if item.get("product_id") or item.get("id")]
            state.reference_context = {
                "candidate_set": [{"product_id": item_id, "position": position + 1, "source": "PRODUCT_BROWSE"} for position, item_id in enumerate(state.recommendation_candidates)],
                "focused_product_id": state.focused_product.get("product_id") if state.focused_product else None,
                "last_updated_turn": state.turn_count,
            }
            state.known_facts["recommendations"] = items
            state.known_facts["recommendation_context"] = {
                **state.known_facts.get("recommendation_context", {}),
                "previous_product_ids": list(state.recommendation_candidates),
            }
            if items:
                state.known_facts["response_attachments"] = [
                    {"type": "image", "url": f"/api/v1/media/{media['media_id']}", "alt": media.get("alt", "商品图片")}
                    for item in items[:3] for media in list_media(product_id=item.get("product_id") or item.get("id"))
                ]
                if action.arguments.get("category") in (None, "面包", "食品"):
                    categories = list(dict.fromkeys(item.get("category") for item in items if item.get("category") and item.get("category") != "早餐"))
                    category_text = "、".join(categories[:5])
                    reply = f"有的，我们店里目前有{category_text}等多种面包。您更想看哪一类？如果没有特别偏好，我也可以按早餐、低糖或适合小朋友来帮您推荐。"
                else:
                    reply = "当前有货的商品有：" + "；".join(f"{item['name']}（{item['price']}元）" for item in items) + "。"
            else:
                reply = "这个品类当前暂时没有可售商品。"
        elif action.tool_name == "compare_products" and result.ok:
            data = result.data
            state.known_facts["comparison"] = data
            cheapest = data["cheapest"]
            if len(data["products"]) > 1:
                reply = f"{cheapest['name']}最便宜，{cheapest['price']}元，比其中最贵的商品便宜{data['difference']}元。"
            else:
                reply = f"{cheapest['name']}目前是{cheapest['price']}元。"
        elif action.tool_name == "explain_product_fit" and result.ok:
            data = result.data
            state.known_facts["product_fit"] = data
            if data["fit_status"] == "SUPPORTED":
                if data.get("concern") == "texture":
                    reply = f"可以的，{data['product_name']}在店内资料中有相应的口感信息，您可以优先考虑。实际口感也会受出炉时间和加热方式影响。"
                else:
                    reply = f"可以的，{data['product_name']}目前有适合{data.get('audience') or '该人群'}的资料标注，作为日常面包是可以考虑的。您更喜欢咸香一点，还是口感柔软一点的呢？"
            elif data["fit_status"] == "NOT_SUPPORTED":
                reply = f"这款目前没有{data.get('audience') or '该人群'}的适配标注，我不想只凭商品名称替您下结论。您如果在意口感或甜度，我可以按这些条件再帮您挑选。"
            else:
                reply = f"我先跟您说明一下：店内资料暂时不足以判断{data['product_name']}是否适合{data.get('audience') or '该人群'}，不建议仅凭名称判断。要不要我按口感和甜度再帮您选几款？"
        elif action.tool_name == "get_sales_policy" and result.ok:
            policy = result.data
            state.known_facts["sales_policy"] = policy
            discounts = "、".join(rule.get("label", "") for rule in policy.get("threshold_discounts", []))
            reply = f"当前优惠包括：{discounts}；满{policy.get('free_shipping_threshold')}元包邮，未满包邮门槛运费{policy.get('shipping_fee')}元。"
        elif action.tool_name == "edit_selected_items" and result.ok:
            state.known_facts["selected_products"] = result.data["items"]
            quote = execute("calculate_order_quote", {"items": result.data["items"], "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode})
            if quote.ok:
                state.quote_context = _quote_context(quote.data, state.known_facts.get("customer_type", "REGULAR"))
                state.known_facts["quote_context"] = {**state.quote_context.model_dump(), "quote_status": "DRAFT", "last_quote_total": quote.data["total"]}
                detail = "；".join(f"{item['name']}×{item['quantity']}={item['subtotal']}元" for item in quote.data["items"])
                reply = f"已更新商品，合计 {quote.data['total']} 元（{detail}）。"
            else:
                reply = "商品已更新，但暂时无法计算报价。"
        elif action.tool_name == "check_selected_items_inventory" and result.ok:
            unavailable = [item for item in result.data if not item.get("available") or (item.get("available_quantity") or 0) < item.get("requested_quantity", 1)]
            if unavailable:
                reply = "当前库存不足：" + "；".join(f"{item['name']}可售{item.get('available_quantity') or 0}件，需要{item['requested_quantity']}件" for item in unavailable) + "。"
            else:
                reply = "当前选择的商品都有货，库存满足所需数量。"
        elif action.tool_name in {"calculate_total", "calculate_order_quote"} and result.ok:
            reply = compose_response(ResponseContext(
                user_text=ctx["text"], action="REQUOTE", business_result=result.data,
            ))
            state.delivery_mode = result.data.get("delivery_mode", state.delivery_mode)
            state.known_facts["delivery_mode"] = state.delivery_mode
            state.quote_context = _quote_context(result.data, action.arguments.get("customer_type", "REGULAR"))
            state.status = "IN_PROGRESS"
            state.missing_slots = []
            state.known_facts["quote_context"] = {**state.quote_context.model_dump(), "quote_status": "DRAFT", "last_quote_total": result.data["total"]}
            if any(goal["type"] == "INVENTORY_CHECK" and goal["status"] == "ACTIVE" for goal in state.goals):
                inventory = execute("check_selected_items_inventory", {"items": result.data["items"]})
                record(state.session_id, {"step_type": "replan_tool_call", "tool_name": "check_selected_items_inventory", "arguments": {"items": result.data["items"]}, "result": inventory.model_dump()}, ctx["run_id"])
                state.tool_results.append(inventory.model_dump())
                if inventory.ok:
                    unavailable = [item for item in inventory.data if not item.get("available") or (item.get("available_quantity") or 0) < item.get("requested_quantity", 1)]
                    reply += " " + ("当前库存不足：" + "；".join(f"{item['name']}可售{item.get('available_quantity') or 0}件，需要{item.get('requested_quantity', 1)}件" for item in unavailable) + "。" if unavailable else "当前选择的商品都有货，库存满足所需数量。")
        elif action.tool_name == "recommend_products" and result.ok:
            recommendation_constraints = normalize_constraints(action.arguments.get("constraints", {}))
            previous_context = state.known_facts.get("recommendation_context", {})
            state.known_facts["recommendation_constraints"] = action.arguments
            state.known_facts["recommendation_metadata"] = {
                "relaxation_options": relaxation_options(recommendation_constraints)
            }
            state.known_facts["recommendation_context"] = {
                "constraints": recommendation_constraints,
                "previous_product_ids": [item["id"] for item in result.data],
                "excluded_product_ids": action.arguments.get("exclude_product_ids", []),
                "last_recommendation_reason": "CONSTRAINT_REFINEMENT" if previous_context else "INITIAL_RECOMMENDATION",
            }
            state.known_facts["recommendations"] = result.data
            state.recommendation_candidates = [item["id"] for item in result.data]
            attachments = []
            generic_request = not any(recommendation_constraints.get(key) for key in ("audience", "texture", "flavor", "sweetness", "budget"))
            if generic_request:
                attachments.extend({"type": "image", "url": f"/api/v1/media/{item['media_id']}", "alt": item.get("alt", "必吃榜")} for item in list_media(asset_type="FEATURED_BOARD"))
            for item in result.data:
                attachments.extend({"type": "image", "url": f"/api/v1/media/{media['media_id']}", "alt": media.get("alt", item["name"])} for media in item.get("media", []))
            state.known_facts["response_attachments"] = attachments
            state.missing_slots = [{"name": "quantity", "prompt": "您需要几个呢？", "priority": 1}]
            state.status = "WAITING_SELECTION"
            reply = render_recommendations(result.data, action.arguments)
        elif action.tool_name == "answer_store_faq" and result.ok:
            state.known_facts["faq"] = result.data
            reply = result.data["message"]
        elif action.tool_name == "reserve_product":
            if result.ok:
                reservation = result.data
                state.known_facts.setdefault("reservations", []).append(reservation)
                state.status = "RESOLVED"
                reply = f"好的，已为您留好{reservation['name']} {reservation['quantity']}个，预计{reservation['pickup_time']}到店取。"
            elif result.reason == "INSUFFICIENT_STOCK":
                data = result.data or {}
                reply = f"不好意思，{data.get('name', '这款商品')}目前可售{data.get('available_quantity', 0)}个，无法为您留{data.get('requested_quantity', 1)}个。"
            else:
                reply = "暂时无法确认留货，请稍后再试或联系门店。"
        else:
            reply = "我暂时无法验证这项信息，建议转人工处理。"
    else:
        reply = action.message or "请补充一些信息。"
        if action.type == "ASK_CONFIRMATION":
            state.requires_confirmation = True
            state.status = "WAITING_CONFIRMATION"
        elif action.type == "ASK_USER":
            state.status = "WAITING_SELECTION" if output.reason_code == "SELECTION_QUANTITY_REQUIRED" else "WAITING_USER"
        elif action.type == "HANDOFF":
            state.requires_human = True
            state.status = "HANDOFF"
            return {"state": state, "reply": reply, "trace": trace, "handoff_reason": output.reason_code}
    followup_accepted = bool(state.known_facts.pop("pending_followup_accepted", False))
    followup_offer = (
        "要不要" in reply
        or any(phrase in reply for phrase in ("可以按", "可以继续", "帮您挑", "帮您推荐", "再帮您"))
    )
    if not followup_accepted and followup_offer and any(word in reply for word in ("推荐", "挑选", "筛选", "口感", "甜度")):
        constraints = state.known_facts.get("understanding", {}).get("constraints", {})
        state.pending_followup = PendingFollowup(
            type="RECOMMEND_PRODUCTS",
            source_turn_id=f"{state.session_id}:{state.turn_count}",
            prompt=reply,
            constraints=constraints,
            context={"product_fit": state.known_facts.get("product_fit", {})},
        )
        _lineage(state, "PENDING_FOLLOWUP", _state_snapshot(state), state.pending_followup.model_dump(), __import__("time").perf_counter())
    return {"state": state, "reply": reply, "trace": trace}


def _quote_context(data: dict, customer_type: str = "REGULAR"):
    from .contracts import QuoteContext
    return QuoteContext(
        items=data.get("items", []), subtotal=data.get("subtotal", 0), discount=data.get("discount", 0),
        shipping=data.get("shipping", 0), total=data.get("total", 0), currency="CNY", status="DRAFT",
        discount_breakdown=data.get("discount_breakdown", {}), customer_type=customer_type,
        next_promotion=data.get("next_promotion"), calculated_at=data.get("calculated_at"),
        delivery_mode=data.get("delivery_mode", "PICKUP"),
    )


def _update_state(ctx: TurnGraphState) -> dict:
    state = ctx["state"]
    reply = ctx.get("reply", "")
    if reply:
        state.add_message("assistant", reply)
    if ctx.get("handoff_reason"):
        create_handoff(state, ctx["handoff_reason"])
    if state.status == "RESOLVED":
        update_goal_status(state, "COMPLETED")
    elif state.status == "HANDOFF":
        update_goal_status(state, "BLOCKED")
    trace = ctx.get("trace", {})
    trace["status"] = state.status
    _lineage(state, "STATE_MANAGER", _state_snapshot(state), {"status": state.status, "reply": reply}, __import__("time").perf_counter())
    _lineage(state, "RESPONSE_GENERATION", _state_snapshot(state), {"reply": reply}, __import__("time").perf_counter())
    return {"state": state, "reply": reply, "trace": trace}


def _evaluate(ctx: TurnGraphState) -> dict:
    state = ctx["state"]
    evaluation = evaluate_turn(state, ctx.get("trace", {}))
    state.turn_evaluations.append(evaluation.model_dump())
    record(state.session_id, {"step_type": "turn_evaluation", "component": "TURN_EVALUATOR", "output": evaluation.model_dump(), "status": "PASS" if not evaluation.failure_component else "FAIL", "error_code": evaluation.failure_component}, ctx["run_id"])
    ctx["trace"]["evaluation"] = evaluation.model_dump()
    finish_run(ctx["run_id"], ctx["state"].status)
    return {"state": ctx["state"], "reply": ctx.get("reply", ""), "trace": ctx.get("trace", {})}


def build_graph():
    """Compile the replaceable load → understand → plan → route → update → evaluate flow."""
    from langgraph.graph import END, START, StateGraph

    workflow = StateGraph(TurnGraphState)
    workflow.add_node("load_context", _load_context)
    workflow.add_node("understand", _understand)
    workflow.add_node("apply_converged_mutation", _apply_converged_mutation)
    workflow.add_node("select_converged_path", _select_converged_path)
    workflow.add_node("converged_short_path", _converged_short_path)
    workflow.add_node("supervisor", _supervise)
    workflow.add_node("update_goal_stack", _update_goal_stack)
    workflow.add_node("resolve_capabilities", _resolve_capabilities)
    workflow.add_node("planner", _planner)
    workflow.add_node("validate_plan", _validate)
    workflow.add_node("policy_gate", _policy_gate)
    workflow.add_node("route", _route)
    workflow.add_node("update_state", _update_state)
    workflow.add_node("evaluate", _evaluate)
    workflow.add_edge(START, "load_context")
    workflow.add_edge("load_context", "understand")
    workflow.add_edge("understand", "apply_converged_mutation")
    workflow.add_edge("apply_converged_mutation", "select_converged_path")
    workflow.add_conditional_edges(
        "select_converged_path",
        _route_after_path_selection,
        {"short_path": "converged_short_path", "supervisor": "supervisor"},
    )
    workflow.add_edge("converged_short_path", "route")
    workflow.add_edge("supervisor", "update_goal_stack")
    workflow.add_edge("update_goal_stack", "resolve_capabilities")
    workflow.add_edge("resolve_capabilities", "planner")
    workflow.add_edge("planner", "validate_plan")
    workflow.add_edge("validate_plan", "policy_gate")
    workflow.add_edge("policy_gate", "route")
    workflow.add_edge("route", "update_state")
    workflow.add_edge("update_state", "evaluate")
    workflow.add_edge("evaluate", END)
    return workflow.compile()


def run_turn(state: CustomerServiceState, text: str, confirmed: bool = False) -> tuple[CustomerServiceState, str, dict]:
    """Unified public entry point: every turn runs through the compiled LangGraph."""
    result = build_graph().invoke({"state": state.model_dump(), "text": text, "confirmed": confirmed})
    final_state = CustomerServiceState.model_validate(result["state"])
    state.__dict__.update(final_state.__dict__)
    return state, result["reply"], result["trace"]
