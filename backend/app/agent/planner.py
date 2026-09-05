import asyncio
import json
import os
import re
import threading

from .contracts import Goal, NextAction, PlannerDecision, PlannerOutput
from .goal_stack import infer_goal_types
from ..llm import get_provider
from ..domain.catalog import PRODUCTS
from .state import CustomerServiceState
from .recommendation_planner_rules import recommendation_arguments
from .reference_resolver import resolve_reference, reference_product


def _deterministic_plan(state: CustomerServiceState, text: str) -> PlannerOutput | None:
    lower = text.lower()
    if "".join(text.strip().split()).lower() in {"好", "好的", "可以", "行", "haode", "ok"} and state.known_facts.get("recommendations"):
        return PlannerOutput(
            goal=Goal(type="PRODUCT_RECOMMENDATION"),
            next_action=NextAction(type="ASK_USER", message="好的，刚才推荐的商品都可以继续下单。请告诉我您想要哪一款和数量。"),
            reason_code="RECOMMENDATION_CONTEXT_ACKNOWLEDGED",
            current_goal_id=_goal_id(state, "PRODUCT_RECOMMENDATION"),
        )
    if state.known_facts.get("understanding_status") == "FAILED":
        return PlannerOutput(goal=Goal(type="OTHER", status="BLOCKED"), next_action=NextAction(type="ASK_USER", message="我暂时没能准确理解这句话。请告诉我商品名称、数量，或您想查询库存还是计算价格。"), reason_code="LLM_OUTPUT_INVALID", missing_information=["understanding"], current_goal_id="goal_unknown")
    current_goals = state.known_facts.get("understanding", {}).get("goals", [])
    actionable_followup = (
        any(char.isdigit() for char in text)
        or any(word in text for word in ("一个", "两个", "三个", "第一个", "第二个", "那个", "最便宜", "多少钱", "有货", "库存", "+"))
        or bool(state.recommendation_candidates)
        or bool(state.known_facts.get("recommendations"))
    )
    # A delivery conversation may legitimately span several turns without a
    # new business keyword. Keep the slot-filling workflow active instead of
    # treating a reminder such as “不是告诉你了吗” as a clarification loop.
    if state.missing_slots and state.delivery_mode == "SHIPPING" and not state.known_facts.get("understanding", {}).get("slot_values"):
        state.known_facts["slot_update_status"] = "UNCHANGED"
        next_slot = state.missing_slots[0]
        return PlannerOutput(
            goal=Goal(type="SHIPPING_POLICY"),
            next_action=NextAction(type="ASK_USER", message=next_slot.get("prompt", "请补充配送信息。")),
            reason_code="DELIVERY_SLOT_REQUIRED",
            missing_information=[next_slot.get("name", "delivery_slot")],
            current_goal_id=_goal_id(state, "SHIPPING_POLICY"),
        )
    pending_delivery_context = bool(state.delivery_slots or state.missing_slots)
    if state.turn_count >= 3 and not state.known_facts.get("goal") and not current_goals and not actionable_followup and not pending_delivery_context:
        state.known_facts["handoff_offer"] = True
        return PlannerOutput(goal=Goal(type="OTHER"), next_action=NextAction(type="ASK_USER", message="我连续几轮还没能准确帮您处理。您可以继续补充商品、订单或服务信息；如果方便，也可以选择转人工，由人工客服接手。"), reason_code="CLARIFICATION_ESCALATION_OFFER", current_goal_id="goal_unknown")
    if any(x in text for x in ["人工", "客服人员", "赔偿", "法律"]):
        return PlannerOutput(goal=Goal(type="OTHER", status="BLOCKED"), next_action=NextAction(type="HANDOFF", message="我为你转接人工客服，已保留当前对话。"), reason_code="HUMAN_REQUEST_OR_HIGH_RISK", current_goal_id="goal_unknown")
    if any(x in text for x in ["退", "换"]):
        state.known_facts["goal"] = "RETURN"
        order_id = state.known_facts.get("order_id")
        if not order_id:
            return PlannerOutput(goal=Goal(type="RETURN"), next_action=NextAction(type="TOOL_CALL", tool_name="find_recent_orders", arguments={"customer_id": state.customer_id or "CUS001"}), reason_code="ORDER_NOT_IDENTIFIED", current_goal_id=_goal_id(state, "RETURN"))
        if not state.known_facts.get("eligibility"):
            return PlannerOutput(goal=Goal(type="RETURN"), next_action=NextAction(type="TOOL_CALL", tool_name="check_return_eligibility", arguments={"order_id": order_id, "customer_id": state.customer_id or "CUS001"}), reason_code="ELIGIBILITY_REQUIRED", current_goal_id=_goal_id(state, "RETURN"))
        if not state.requires_confirmation:
            return PlannerOutput(goal=Goal(type="RETURN"), next_action=NextAction(type="ASK_CONFIRMATION", message="订单符合当前退货规则。是否确认提交退货申请？"), reason_code="RETURN_CONFIRMATION_REQUIRED", requires_confirmation=True, current_goal_id=_goal_id(state, "RETURN"))
    understanding = state.known_facts.get("understanding", {})
    resolved_items = _resolved_items(state)

    # Category-only browsing is a complete read-only action. Once the
    # understanding layer has identified the category, do not ask the LLM
    # Planner to invent a product-level plan or capability combination.
    from .understanding import _short_category_reference
    category_from_turn = _short_category_reference(text)
    category_from_understanding = understanding.get("constraints", {}).get("category")
    browse_category = category_from_understanding or category_from_turn
    if browse_category and not resolved_items:
        state.known_facts["goal"] = "PRODUCT_BROWSE"
        return PlannerOutput(
            goal=Goal(type="PRODUCT_BROWSE"),
            next_action=NextAction(
                type="TOOL_CALL",
                tool_name="list_available_inventory",
                arguments={"category": browse_category},
            ),
            reason_code="CATEGORY_BROWSE_DETERMINISTIC",
            current_goal_id=_goal_id(state, "PRODUCT_BROWSE"),
        )
    reservation_text = any(word in text for word in ("帮我留", "帮我预留", "留一个", "留两个", "预留一个", "预留两个")) or ("还有" in text and "要" in text and "个" in text and bool(resolved_items))
    pending_reservation = state.known_facts.get("pending_reservation")
    if reservation_text or pending_reservation:
        items = resolved_items or (pending_reservation or {}).get("items", [])
        if items:
            pickup_match = re.search(r"([上下]午)?\s*(\d{1,2}|一|两|二|三|四|五|六|七|八|九|十)(?::\d{2})?点", text)
            pickup_time = pickup_match.group(0) if pickup_match else (pending_reservation or {}).get("pickup_time")
            if not pickup_time:
                state.known_facts["pending_reservation"] = {"items": items}
                state.missing_slots = [{"name": "pickup_time", "prompt": "好的，请告诉我预计几点到店取？", "priority": 1}]
                state.status = "WAITING_USER"
                return PlannerOutput(goal=Goal(type="RESERVATION"), next_action=NextAction(type="ASK_USER", message="好的，请告诉我预计几点到店取？"), reason_code="RESERVATION_PICKUP_TIME_REQUIRED", missing_information=["pickup_time"], current_goal_id=_goal_id(state, "RESERVATION"))
            item = items[0]
            state.known_facts.pop("pending_reservation", None)
            return PlannerOutput(goal=Goal(type="RESERVATION"), next_action=NextAction(type="TOOL_CALL", tool_name="reserve_product", arguments={"product_id": item["product_id"], "quantity": item.get("quantity", 1), "customer_id": state.customer_id or "CUS001", "pickup_time": pickup_time, "reservation_key": f"{state.session_id}:{item['product_id']}:{item.get('quantity', 1)}"}), reason_code="RESERVATION_REQUIRED", current_goal_id=_goal_id(state, "RESERVATION"))
    early_quantity_match = re.search(r"(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个", text)
    if state.known_facts.get("selected_products") and "还是" in text and early_quantity_match:
        items = [dict(item) for item in state.known_facts["selected_products"]]
        state.known_facts["preserve_selection"] = True
        return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="SELECTION_CONFIRMED_UNCHANGED", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    state.conversation_act = understanding.get("conversation_act", "REQUEST")
    incoming_slots = {key: value for key, value in understanding.get("slot_values", {}).items() if value not in (None, "", [], {})}
    previous_slots = dict(state.delivery_slots)
    state.delivery_slots.update(incoming_slots)
    if incoming_slots:
        state.known_facts["slot_update_status"] = "UPDATED"
    elif previous_slots:
        state.known_facts["slot_update_status"] = "UNCHANGED"
    else:
        state.known_facts["slot_update_status"] = "NO_SLOT_INPUT"
    delivery_mode = understanding.get("delivery_mode", "UNKNOWN")
    if delivery_mode in {"PICKUP", "SHIPPING"}:
        state.delivery_mode = delivery_mode
        state.known_facts["delivery_mode"] = delivery_mode
    if delivery_mode == "PICKUP" and state.quote_context and state.quote_context.items:
        return PlannerOutput(
            goal=Goal(type="PRICE_CALCULATION"),
            next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": state.quote_context.items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": delivery_mode}),
            reason_code="DELIVERY_MODE_UPDATED",
            current_goal_id=_goal_id(state, "PRICE_CALCULATION"),
        )

    # Consume a validated category browse intent before any product-required
    # fallback.  A terse follow-up such as “那吐司呢？” has no SKU, but it
    # is still fully actionable as a category inventory list.
    browse_category = understanding.get("constraints", {}).get("category")
    if "PRODUCT_BROWSE" in understanding.get("goals", []) and browse_category:
        state.known_facts["goal"] = "PRODUCT_BROWSE"
        return PlannerOutput(
            goal=Goal(type="PRODUCT_BROWSE"),
            next_action=NextAction(
                type="TOOL_CALL",
                tool_name="list_available_inventory",
                arguments={"category": browse_category},
            ),
            reason_code="CATEGORY_BROWSE_FROM_UNDERSTANDING",
            current_goal_id=_goal_id(state, "PRODUCT_BROWSE"),
        )

    # Complete a pending selection when the customer answers only the slot
    # requested in the previous turn, e.g. “两个”.
    pending_selection = state.known_facts.get("pending_selection")
    if pending_selection and state.missing_slots and re.fullmatch(r"\s*(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个?\s*", text):
        quantity_text = re.search(r"(\d+|一|两|二|三|四|五|六|七|八|九|十)", text).group(1)
        quantity = int(quantity_text) if quantity_text.isdigit() else {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}[quantity_text]
        selected = {**pending_selection, "quantity": quantity, "operation": "ADD"}
        items = _apply_operations(state.known_facts.get("selected_products", []), [selected])
        state.known_facts["selected_products"] = items
        state.known_facts.pop("pending_selection", None)
        state.missing_slots = []
        state.status = "IN_PROGRESS"
        return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="SELECTION_SLOT_FILLED", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    # Resolve quantity-only mutations before inheriting a prior recommendation
    # goal. This lets “第一款要两个/再来一个/改成一个” operate on the
    # focused, selected, or ranked recommendation item.
    quantity_only_match = re.search(r"(?:(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个|\+\s*(\d+))", text)
    raw_resolved = state.known_facts.get("resolved_products", [])
    category_updates = [item for item in raw_resolved if item.get("operation") == "SET_QUANTITY" and item.get("query")]
    quantity_only = bool(quantity_only_match and not resolved_items and not category_updates and ("+" in text or any(word in text for word in ("再来", "来", "加", "要", "改成", "变成", "调整为", "第一款", "第二款", "第三款"))))
    if quantity_only:
        reference = resolve_reference(state, text=text)
        if reference.get("reference_type") == "AMBIGUOUS":
            return PlannerOutput(goal=Goal(type="PRODUCT_SELECTION"), next_action=NextAction(type="ASK_USER", message="您是指刚才哪一款商品呢？"), reason_code="AMBIGUOUS_REFERENCE", missing_information=["product_reference"], current_goal_id=_goal_id(state, "PRODUCT_SELECTION"))
        reference_item = reference_product(state, reference)
        if reference_item:
            raw_quantity = quantity_only_match.group(1) or quantity_only_match.group(2)
            quantity = int(raw_quantity) if raw_quantity.isdigit() else {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}[raw_quantity]
            is_increment = any(word in text for word in ("再来", "再加", "加一个", "增加一个"))
            selected = [dict(reference_item)]
            selected[0]["quantity"] = int(selected[0].get("quantity", 0)) + quantity if is_increment else quantity
            selected[0]["selection_status"] = "CONFIRMED"
            selected[0]["source"] = "reference_resolution"
            state.known_facts["selected_products"] = selected
            return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": selected, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="QUANTITY_UPDATED_FROM_CONTEXT", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    # A category-level mutation such as “贝果改成三个” must target only the
    # already selected items in that category. The resolver may return
    # candidates rather than inventing an SKU, so this remains deterministic.
    if category_updates:
        selected = [dict(item) for item in state.known_facts.get("selected_products", [])]
        changed = False
        for update in category_updates:
            for item in selected:
                product = next((product for product in PRODUCTS if product["id"] == item.get("product_id")), None)
                if product and product.get("category") == update.get("query"):
                    item["quantity"] = update.get("quantity", 1)
                    changed = True
        if changed:
            state.known_facts["selected_products"] = selected
            return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": selected, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="CATEGORY_QUANTITY_UPDATED", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    if understanding.get("requires_clarification"):
        return PlannerOutput(goal=Goal(type="OTHER"), next_action=NextAction(type="ASK_USER", message="您是想问适合老人吃的面包，还是想了解老人什么时候适合吃呢？"), reason_code="AMBIGUOUS_REQUEST", current_goal_id=_goal_id(state, "OTHER"))
    explicit_price_words = any(x in text for x in ("多少钱", "多收钱", "合计", "总价", "一起要", "一共多少", "算一下", "算算"))
    direct_inventory_product = _find_product(text)
    direct_inventory_query = direct_inventory_product is not None and any(x in text for x in ("有", "有货", "库存", "还有", "吗", "么")) and not explicit_price_words
    if "PRODUCT_FIT_QUERY" in understanding.get("goals", []):
        item = next((item for item in resolved_items if item.get("product_id")), None)
        if not item and state.focused_product and state.focused_product.get("product_id"):
            item = dict(state.focused_product)
        if not item and len(state.quote_context.items) == 1:
            item = dict(state.quote_context.items[0])
        if item:
            constraints = understanding.get("constraints", {})
            semantic = understanding.get("semantic_state", {})
            audience = constraints.get("audience") or semantic.get("who", {}).get("audience")
            concern = constraints.get("concern") or ("texture" if any(word in text for word in ("硬", "软", "口感")) else "audience")
            return PlannerOutput(goal=Goal(type="PRODUCT_FIT_QUERY"), next_action=NextAction(type="TOOL_CALL", tool_name="explain_product_fit", arguments={"product_id": item["product_id"], "audience": audience, "concern": concern}), reason_code="PRODUCT_FIT_REQUIRED", current_goal_id=_goal_id(state, "PRODUCT_FIT_QUERY"))
    if direct_inventory_query and len(resolved_items) > 1 and not state.known_facts.get("selected_products"):
        return PlannerOutput(goal=Goal(type="INVENTORY_CHECK"), next_action=NextAction(type="TOOL_CALL", tool_name="check_selected_items_inventory", arguments={"items": resolved_items}), reason_code="MULTI_PRODUCT_INVENTORY_REQUIRED", current_goal_id=_goal_id(state, "INVENTORY_CHECK"))
    if direct_inventory_query and not state.known_facts.get("selected_products"):
        state.known_facts["goal"] = "INVENTORY_CHECK"
        return PlannerOutput(goal=Goal(type="INVENTORY_CHECK"), next_action=NextAction(type="TOOL_CALL", tool_name="check_inventory", arguments={"product_id": direct_inventory_product["id"]}), reason_code="INVENTORY_REQUIRED", current_goal_id=_goal_id(state, "INVENTORY_CHECK"))
    operation_edit = bool(resolved_items) and all(item.get("operation") != "ADD" for item in resolved_items)
    price_request = (bool(set(understanding.get("goals", [])) & {"PRICE_CALCULATION"}) or explicit_price_words) and not (operation_edit and not explicit_price_words)
    member_question = "会员" in text and any(word in text for word in ("优惠", "会员价", "折扣", "便宜"))
    # A complete current-turn item list replaces the working set. Only
    # explicit additive language should merge with selected_products;
    # otherwise the same ADD operation can be applied twice and double the
    # requested quantities before quoting.
    if price_request and resolved_items and any(item.get("name") and item.get("name") in text for item in resolved_items):
        if not any(word in text for word in ("再加", "再来", "增加", "另外")):
            items = [dict(item) for item in resolved_items]
            state.known_facts["selected_products"] = items
            state.known_facts["goal"] = "PRICE_CALCULATION"
            return PlannerOutput(
                goal=Goal(type="PRICE_CALCULATION"),
                next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}),
                reason_code="CURRENT_TURN_ITEMS_QUOTE",
                current_goal_id=_goal_id(state, "PRICE_CALCULATION"),
            )
    if state.quote_context and (member_question or (state.delivery_mode != "SHIPPING" and any(goal in understanding.get("goals", []) for goal in ("SHIPPING_POLICY", "MEMBERSHIP_PRICING")))):
        if member_question:
            state.known_facts["customer_type"] = "MEMBER"
        goal_type = "MEMBERSHIP_PRICING" if member_question or "MEMBERSHIP_PRICING" in understanding.get("goals", []) else "SHIPPING_POLICY"
        return PlannerOutput(goal=Goal(type=goal_type), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": state.quote_context.items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="POLICY_RECALCULATION", current_goal_id=_goal_id(state, goal_type))

    pending_delivery = state.status == "WAITING_USER" and (
        bool(state.delivery_slots)
        or any(slot.get("name") in {"delivery_address", "recipient_name", "phone"} for slot in state.missing_slots)
    )
    current_non_shipping = bool(set(understanding.get("goals", [])) & {"PRODUCT_RECOMMENDATION", "PRODUCT_BROWSE", "PRODUCT_FIT_QUERY", "PRODUCT_COMPARE", "FAQ", "INVENTORY_CHECK"})
    has_shipping_goal = not current_non_shipping and (pending_delivery or any(goal.get("type") == "SHIPPING_POLICY" and goal.get("status") == "ACTIVE" for goal in state.goals))
    if understanding.get("delivery_intent") or "SHIPPING_POLICY" in understanding.get("goals", []) or has_shipping_goal:
        from .slot_manager import next_clarification
        clarification = next_clarification("CREATE_DELIVERY_REQUEST", state.delivery_slots)
        if clarification:
            state.missing_slots = [slot.model_dump() for slot in clarification.missing_slots]
            return PlannerOutput(goal=Goal(type="SHIPPING_POLICY"), next_action=NextAction(type="ASK_USER", message=clarification.missing_slots[0].prompt), reason_code="DELIVERY_SLOT_REQUIRED", missing_information=[clarification.next_slot or "delivery_address"], current_goal_id=_goal_id(state, "SHIPPING_POLICY"))

    # Slicing remains FAQ; reservation is handled above with inventory safety.
    if "FAQ" in understanding.get("goals", []) and "RESERVATION" not in understanding.get("goals", []):
        return PlannerOutput(goal=Goal(type="FAQ"), next_action=NextAction(type="TOOL_CALL", tool_name="answer_store_faq", arguments={"question": text}), reason_code="STORE_FAQ_REQUIRED", current_goal_id=_goal_id(state, "FAQ"))

    # A resolved product plus an explicit selection/quantity is a state
    # mutation, not another recommendation request. Quantity is deliberately
    # clarified instead of silently defaulting to one for a purchase choice.
    quantity_match = re.search(r"(?:(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个|\+\s*(\d+))", text)
    # Confirmation language must be handled before generic selection logic;
    # “吐司还是一个” keeps the existing working set unchanged.
    if state.known_facts.get("selected_products") and "还是" in text and quantity_match:
        items = [dict(item) for item in state.known_facts["selected_products"]]
        return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="SELECTION_CONFIRMED_UNCHANGED", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    explicit_selection = bool(resolved_items) and (
        state.conversation_act in {"SELECT", "ADD", "ACCEPT"}
        or any(word in text for word in ("要", "买", "来", "需要"))
        or bool(quantity_match)
    ) and not any(word in text for word in ("推荐", "适合", "有什么", "哪些", "有货", "库存", "还能买", "买吗", "不要", "去掉", "删除", "改成", "换成"))
    if explicit_selection:
        if not quantity_match and not understanding.get("slot_values", {}).get("quantity"):
            state.known_facts["pending_selection"] = dict(resolved_items[0])
            state.missing_slots = [{"name": "quantity", "prompt": "您需要几个呢？", "priority": 1}]
            state.status = "WAITING_SELECTION"
            return PlannerOutput(
                goal=Goal(type="PRODUCT_SELECTION"),
                next_action=NextAction(type="ASK_USER", message=f"好的，{resolved_items[0].get('name', '这款商品')}可以的。您需要几个呢？"),
                reason_code="SELECTION_QUANTITY_REQUIRED", missing_information=["quantity"], current_goal_id=_goal_id(state, "PRODUCT_SELECTION"),
            )
        items = _apply_operations(state.known_facts.get("selected_products", []), resolved_items)
        state.known_facts["selected_products"] = items
        state.missing_slots = []
        state.known_facts["recommendation_selected"] = [item["product_id"] for item in items]
        state.known_facts["goal"] = "PRICE_CALCULATION"
        return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="ITEM_SELECTED_QUOTE_REQUIRED", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    if "PROMOTION_QUERY" in understanding.get("goals", []):
        return PlannerOutput(goal=Goal(type="PROMOTION_QUERY"), next_action=NextAction(type="TOOL_CALL", tool_name="get_sales_policy", arguments={}), reason_code="PROMOTION_POLICY_REQUIRED", current_goal_id=_goal_id(state, "PROMOTION_QUERY"))
    if "FAQ" in understanding.get("goals", []):
        return PlannerOutput(goal=Goal(type="FAQ"), next_action=NextAction(type="TOOL_CALL", tool_name="answer_store_faq", arguments={"question": text}), reason_code="STORE_FAQ_REQUIRED", current_goal_id=_goal_id(state, "FAQ"))
    explicit_compare = any(word in text for word in ("哪个便宜", "最便宜", "差多少", "比较一下", "哪个更贵", "哪个更便宜"))
    if "PRODUCT_COMPARE" in understanding.get("goals", []) and not explicit_compare:
        # “怎么选” with a budget/count/category is a recommendation request;
        # do not let an over-broad model goal route it to price comparison.
        understanding.setdefault("goals", []).append("PRODUCT_RECOMMENDATION")
    # “最便宜的来两个” is selection plus quantity, not a comparison-only
    # request. Let the reference resolver choose the relative candidate first.
    if "PRODUCT_COMPARE" in understanding.get("goals", []) and explicit_compare and not quantity_match:
        product_ids = [item["product_id"] for item in resolved_items if item.get("product_id")]
        if not product_ids:
            product_ids = [item.get("product_id") or item.get("id") for item in state.known_facts.get("available_products", []) if item.get("product_id") or item.get("id")]
        category = next((category for category in ("贝果", "吐司", "欧包", "盐面包") if category in text), None)
        return PlannerOutput(goal=Goal(type="PRODUCT_COMPARE"), next_action=NextAction(type="TOOL_CALL", tool_name="compare_products", arguments={"product_ids": product_ids, "category": category}), reason_code="PRODUCT_COMPARISON_REQUIRED", current_goal_id=_goal_id(state, "PRODUCT_COMPARE"))
    # A quantity-only follow-up refers to the single confirmed item from the
    # previous turn, e.g. “要2个，多收钱”. Apply it before re-quoting so the
    # conversation state, rather than the current text alone, drives pricing.
    quantity_only = bool(quantity_match and not resolved_items and ("+" in text or any(word in text for word in ("再来", "来", "加", "要", "改成", "变成", "调整为", "第一款", "第二款", "第三款"))))
    if (price_request or quantity_only) and not resolved_items and quantity_match:
        reference = resolve_reference(state, text=text)
        reference_item = reference_product(state, reference)
        if reference.get("reference_type") == "AMBIGUOUS":
            return PlannerOutput(goal=Goal(type="PRODUCT_SELECTION"), next_action=NextAction(type="ASK_USER", message="您是指刚才哪一款商品呢？"), reason_code="AMBIGUOUS_REFERENCE", missing_information=["product_reference"], current_goal_id=_goal_id(state, "PRODUCT_SELECTION"))
        if reference_item:
            raw_quantity = quantity_match.group(1) or quantity_match.group(2)
            quantity = int(raw_quantity) if raw_quantity.isdigit() else {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}[raw_quantity]
            selected = [dict(reference_item)]
            is_increment = any(word in text for word in ("再来", "再加", "加一个", "增加一个"))
            selected[0]["quantity"] = int(selected[0].get("quantity", 0)) + quantity if is_increment else quantity
            selected[0]["selection_status"] = "CONFIRMED"
            selected[0]["source"] = "reference_resolution"
            state.known_facts["selected_products"] = selected
            return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": selected, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="QUANTITY_UPDATED_FROM_CONTEXT", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    # A pronoun/rank reference can still be an inventory question, such as
    # “那个有货吗”. Resolve it against current candidates before asking for a
    # product name; the resolver remains the only SKU authority.
    if not resolved_items and any(word in text for word in ("有货吗", "还有吗", "有吗", "库存")):
        reference = resolve_reference(state, text=text)
        reference_item = reference_product(state, reference)
        if reference_item:
            return PlannerOutput(
                goal=Goal(type="INVENTORY_CHECK"),
                next_action=NextAction(type="TOOL_CALL", tool_name="check_inventory", arguments={"product_id": reference_item["product_id"]}),
                reason_code="REFERENCE_INVENTORY_REQUIRED",
                current_goal_id=_goal_id(state, "INVENTORY_CHECK"),
            )
    if any(goal in understanding.get("goals", []) for goal in ("PRODUCT_RECOMMENDATION", "RECOMMENDATION")):
        state.known_facts["goal"] = "PRODUCT_RECOMMENDATION"
        context = state.known_facts.get("recommendation_context", {})
        arguments = recommendation_arguments(text, context.get("constraints"), understanding.get("constraints"), context.get("previous_product_ids"))
        return PlannerOutput(goal=Goal(type="PRODUCT_RECOMMENDATION"), next_action=NextAction(type="TOOL_CALL", tool_name="recommend_products", arguments=arguments), reason_code="RECOMMENDATION_REQUIRED", current_goal_id=_goal_id(state, "PRODUCT_RECOMMENDATION"))
    if "PRODUCT_BROWSE" in understanding.get("goals", []):
        category = next((item for item in ("贝果", "吐司", "欧包", "盐面包", "小面包") if item in text), None)
        return PlannerOutput(goal=Goal(type="PRODUCT_BROWSE"), next_action=NextAction(type="TOOL_CALL", tool_name="list_available_inventory", arguments={"category": category}), reason_code="PRODUCT_BROWSE_REQUIRED", current_goal_id=_goal_id(state, "PRODUCT_BROWSE"))
    if price_request:
        items = _apply_operations(state.known_facts.get("selected_products", []), resolved_items) or state.known_facts.get("selected_products") or _requested_items(text)
        if not items:
            reference = resolve_reference(state, text=text)
            referenced = reference_product(state, reference)
            if referenced:
                state.focused_product = {"product_id": referenced["product_id"], "name": referenced["name"], "quantity": 1, "unit_price": referenced.get("price") or referenced.get("unit_price", 0), "selection_status": "FOCUSED", "source": "reference_resolution"}
                items = [{"product_id": referenced["product_id"], "name": referenced["name"], "quantity": 1, "unit_price": referenced.get("price") or referenced.get("unit_price", 0), "selection_status": "CONFIRMED", "source": "reference_resolution"}]
    else:
        items = None
    if items:
        if "会员" in text:
            state.known_facts["customer_type"] = "MEMBER"
        state.known_facts["goal"] = "PRICE_CALCULATION"
        state.known_facts["selected_products"] = items
        return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="calculate_order_quote", arguments={"items": items, "customer_type": state.known_facts.get("customer_type", "REGULAR"), "delivery_mode": state.delivery_mode}), reason_code="TOTAL_REQUIRED", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    if resolved_items and any(item.get("operation") != "ADD" for item in resolved_items):
        items = _apply_operations(state.known_facts.get("selected_products", []), resolved_items)
        state.known_facts["selected_products"] = items
        state.known_facts["goal"] = "PRICE_CALCULATION"
        return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="edit_selected_items", arguments={"items": items}), reason_code="SELECTION_UPDATED", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    product = _find_product(text)
    if product is None and resolved_items:
        resolved_id = next((item.get("product_id") for item in resolved_items if item.get("product_id")), None)
        product = next((item for item in PRODUCTS if item["id"] == resolved_id), None)
    resolved_inventory = bool(set(understanding.get("goals", [])) & {"INVENTORY_CHECK"})
    raw_resolved = state.known_facts.get("resolved_products", [])
    exact_resolution = len(raw_resolved) == 1 and raw_resolved[0].get("match_type") == "EXACT_NAME"
    if resolved_items and exact_resolution and resolved_inventory and len(resolved_items) == 1 and not state.known_facts.get("selected_products"):
        state.known_facts["goal"] = "INVENTORY_CHECK"
        return PlannerOutput(
            goal=Goal(type="INVENTORY_CHECK"),
            next_action=NextAction(type="TOOL_CALL", tool_name="check_inventory", arguments={"product_id": resolved_items[0]["product_id"]}),
            reason_code="INVENTORY_REQUIRED",
            current_goal_id=_goal_id(state, "INVENTORY_CHECK"),
        )
    if not resolved_items and understanding.get("product_mentions") and resolved_inventory:
        return None
    category = next((item for item in sorted({p["category"] for p in PRODUCTS}, key=len, reverse=True) if item in text), None)
    generic_availability = any(x in text for x in ("还有什么", "还有哪些", "有什么", "哪些面包"))
    if product and any(word in text for word in ("再加", "增加", "改成", "换成")):
        items = [dict(item) for item in state.known_facts.get("selected_products", [])]
        quantity_match = re.search(r"(\d+|一|两|二|三|四|五)\s*个", text)
        quantity = int(quantity_match.group(1)) if quantity_match and quantity_match.group(1).isdigit() else {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5}.get(quantity_match.group(1), 1) if quantity_match else 1
        existing = next((item for item in items if item["product_id"] == product["id"]), None)
        if "改成" in text or "换成" in text:
            if existing:
                existing["quantity"] = quantity
            else:
                items.append({"product_id": product["id"], "name": product["name"], "quantity": quantity, "unit_price": product["price"], "selection_status": "CONFIRMED", "source": "conversation"})
        else:
            if existing:
                existing["quantity"] = existing.get("quantity", 1) + quantity
            else:
                items.append({"product_id": product["id"], "name": product["name"], "quantity": quantity, "unit_price": product["price"], "selection_status": "CONFIRMED", "source": "conversation"})
        state.known_facts["goal"] = "PRICE_CALCULATION"
        return PlannerOutput(goal=Goal(type="PRICE_CALCULATION"), next_action=NextAction(type="TOOL_CALL", tool_name="edit_selected_items", arguments={"items": items}), reason_code="SELECTION_UPDATED", current_goal_id=_goal_id(state, "PRICE_CALCULATION"))
    inventory_request = bool(set(understanding.get("goals", [])) & {"INVENTORY_CHECK"}) or any(word in text for word in ("这些都有货", "都还有货", "商品都有货"))
    if resolved_items and inventory_request and (len(resolved_items) > 1 or state.known_facts.get("selected_products")):
        items = _apply_operations(state.known_facts.get("selected_products", []), resolved_items) or resolved_items
        state.known_facts["selected_products"] = items
        state.known_facts["goal"] = "INVENTORY_CHECK"
        return PlannerOutput(goal=Goal(type="INVENTORY_CHECK"), next_action=NextAction(type="TOOL_CALL", tool_name="check_selected_items_inventory", arguments={"items": items}), reason_code="SELECTED_ITEMS_INVENTORY_REQUIRED", current_goal_id=_goal_id(state, "INVENTORY_CHECK"))
    if state.known_facts.get("selected_products") and any(word in text for word in ("这些都有货", "都还有货", "商品都有货")):
        state.known_facts["goal"] = "INVENTORY_CHECK"
        return PlannerOutput(goal=Goal(type="INVENTORY_CHECK"), next_action=NextAction(type="TOOL_CALL", tool_name="check_selected_items_inventory", arguments={"items": state.known_facts["selected_products"]}), reason_code="SELECTED_ITEMS_INVENTORY_REQUIRED", current_goal_id=_goal_id(state, "INVENTORY_CHECK"))
    specific_availability = product is not None and (state.known_facts.get("goal") == "INVENTORY_CHECK" or any(x in text for x in ("有", "库存", "有货", "还有", "吗", "么", "呢")))
    if generic_availability and "面包" in text:
        state.known_facts["goal"] = "INVENTORY_CHECK"
        return PlannerOutput(goal=Goal(type="INVENTORY_CHECK"), next_action=NextAction(type="TOOL_CALL", tool_name="list_available_inventory", arguments={"category": "面包"}), reason_code="AVAILABLE_PRODUCTS_REQUIRED", current_goal_id=_goal_id(state, "INVENTORY_CHECK"))
    if category and product is None and (category in {"贝果", "吐司", "欧包", "盐面包", "小面包"} or state.known_facts.get("goal") == "INVENTORY_CHECK"):
        state.known_facts["goal"] = "INVENTORY_CHECK"
        return PlannerOutput(goal=Goal(type="INVENTORY_CHECK"), next_action=NextAction(type="TOOL_CALL", tool_name="list_available_inventory", arguments={"category": category}), reason_code="CATEGORY_INVENTORY_LIST", current_goal_id=_goal_id(state, "INVENTORY_CHECK"))
    if specific_availability or any(x in text for x in ["有货", "库存"]):
        state.known_facts["goal"] = "INVENTORY_CHECK"
        if not product:
            return PlannerOutput(goal=Goal(type="INVENTORY_CHECK"), next_action=NextAction(type="ASK_USER", message="请告诉我想查询的商品和规格。"), reason_code="PRODUCT_REQUIRED", missing_information=["product"], current_goal_id=_goal_id(state, "INVENTORY_CHECK"))
        return PlannerOutput(goal=Goal(type="INVENTORY_CHECK"), next_action=NextAction(type="TOOL_CALL", tool_name="check_inventory", arguments={"product_id": product["id"]}), reason_code="INVENTORY_REQUIRED", current_goal_id=_goal_id(state, "INVENTORY_CHECK"))
    if any(x in text for x in ["推荐", "早餐", "低糖", "适合", "便宜", "不要", "软", "甜", "咸", "口感"]):
        state.known_facts["goal"] = "RECOMMENDATION"
        context = state.known_facts.get("recommendation_context", {})
        arguments = recommendation_arguments(text, context.get("constraints"), understanding.get("constraints"), context.get("previous_product_ids"))
        return PlannerOutput(goal=Goal(type="RECOMMENDATION"), next_action=NextAction(type="TOOL_CALL", tool_name="recommend_products", arguments=arguments), reason_code="RECOMMENDATION_REQUIRED", current_goal_id=_goal_id(state, "RECOMMENDATION"))
    return None


def _find_product(text: str) -> dict | None:
    """Match the longest known product name, including products loaded from seed."""
    return max((product for product in PRODUCTS if product["name"] in text), key=lambda item: len(item["name"]), default=None)


def _requested_items(text: str) -> list[dict]:
    product = _find_product(text)
    if not product:
        return []
    match = re.search(r"(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个", text)
    numbers = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    quantity = int(match.group(1)) if match and match.group(1).isdigit() else numbers.get(match.group(1), 1) if match else 1
    return [{"product_id": product["id"], "name": product["name"], "quantity": quantity, "unit_price": product["price"], "selection_status": "CONFIRMED", "source": "conversation"}]


def _resolved_items(state: CustomerServiceState) -> list[dict]:
    """Convert Resolver output into quote/edit items; Resolver remains the only SKU authority."""
    return [
        {
            "product_id": item["product_id"],
            "name": item["name"],
            "quantity": item.get("quantity", 1),
            "unit_price": next((p["price"] for p in PRODUCTS if p["id"] == item["product_id"]), 0),
            "selection_status": "CONFIRMED",
            "source": "conversation",
            "operation": item.get("operation", "ADD"),
            "query": item.get("query", item["name"]),
            "reference_source": item.get("reference_source"),
        }
        for item in state.known_facts.get("resolved_products", [])
        if item.get("product_id")
    ]


def _apply_operations(current: list[dict], incoming: list[dict]) -> list[dict]:
    items = [dict(item) for item in current]
    for item in incoming:
        operation = item.get("operation", "ADD")
        existing = next((value for value in items if value.get("product_id") == item["product_id"]), None)
        if operation == "REMOVE":
            items = [value for value in items if value is not existing]
        elif operation == "SET_QUANTITY" and existing:
            existing["quantity"] = item.get("quantity", 1)
        elif operation == "KEEP":
            continue
        elif operation == "REPLACE":
            if existing:
                items.remove(existing)
            items.append({key: value for key, value in item.items() if key not in {"operation", "query"}})
        elif existing:
            existing["quantity"] = existing.get("quantity", 1) + item.get("quantity", 1)
        else:
            items.append({key: value for key, value in item.items() if key not in {"operation", "query"}})
    return items


def _goal_id(state: CustomerServiceState, goal_type: str) -> str | None:
    return next((item["id"] for item in state.goals if item["type"] == goal_type), None)


def _run(coro):
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    result = []
    thread = threading.Thread(target=lambda: result.append(asyncio.run(coro)))
    thread.start()
    thread.join()
    return result[0]


def _llm_plan(state: CustomerServiceState, text: str, capabilities: list[str] | None = None) -> PlannerOutput:
    context = {
        "user_message": text,
        "recent_messages": [message.model_dump() for message in state.messages[-8:]],
        "known_facts": state.known_facts,
        "active_goals": state.goals,
        "available_capabilities": capabilities or [],
    }
    try:
        messages = [
            _message("system", '''你是 Shanye Shop 的资深智能客服规划器。你熟悉店内商品、价格、会员价、满减和包邮政策，先理解顾客真实需求，再选择下一步能力；回复应热情、自然、准确，只有在对顾客有帮助时才温和提示促销，不要机械播报“查询时间”。基于上下文、语义理解结果和可用能力选择下一步，不要重新依赖关键词规则。只输出 JSON，字段必须为 goal_type、current_goal_id、action_type、tool_name、tool_args、message、missing_fields、reason_code、expected_state_transition。goal_type 只能是 ORDER_STATUS、RETURN、RECOMMENDATION、INVENTORY_CHECK、PRICE_CALCULATION、PRODUCT_BROWSE、PRODUCT_COMPARE、PRODUCT_RECOMMENDATION、SHIPPING_POLICY、PROMOTION_QUERY、MEMBERSHIP_PRICING、FAQ、OTHER。只能选择 available_capabilities 中的工具。商品查询必须使用语义理解已解析的 product_id；如果用户只说一个品类且有多个候选商品，应调用 list_available_inventory 列出该品类当前有货商品，不要反问具体品种。价格计算必须使用 known_facts 中已确认的 selected_products；没有新商品的报价或政策追问必须复用 quote_context.items。'''),
            _message("user", json.dumps(context, ensure_ascii=False)),
        ]
        decision = None
        for attempt in range(2):
            try:
                decision = _run(get_provider().structured_generate(messages=messages, output_schema=PlannerDecision))
                break
            except Exception:
                if attempt == 1:
                    raise
    except Exception:
        return PlannerOutput(
            goal=Goal(type="OTHER", status="BLOCKED"),
            next_action=NextAction(type="ASK_USER", message="我暂时无法准确理解你的需求，请补充商品、订单或服务类型。"),
            reason_code="LLM_OUTPUT_INVALID",
            missing_information=["goal"],
            current_goal_id="goal_unknown",
        )
    return PlannerOutput(
        goal=Goal(type=decision.goal_type),
        next_action=NextAction(type=decision.action_type, tool_name=decision.tool_name, arguments=decision.tool_args, message=decision.message),
        reason_code=decision.reason_code,
        missing_information=decision.missing_fields,
        current_goal_id=decision.current_goal_id,
        decision_summary=decision.expected_state_transition,
    )


def _message(role: str, content: str):
    from .state import Message
    return Message(role=role, content=content)


def plan(state: CustomerServiceState, text: str, capabilities: list[str] | None = None) -> PlannerOutput:
    """Use LLM planning in production; keep deterministic safety/fallback paths."""
    deterministic = _deterministic_plan(state, text)
    if os.getenv("AGENT_ARCHITECTURE", "legacy").lower() == "semantic":
        return deterministic or PlannerOutput(goal=Goal(type="OTHER"), next_action=NextAction(type="ASK_USER", message="我需要再确认一下您的具体需求。"), reason_code="SEMANTIC_INTENT_UNRESOLVED", current_goal_id="goal_unknown")
    if os.getenv("LLM_PROVIDER", "mock").lower() == "mock":
        return deterministic or _llm_plan(state, text)
    llm_output = _llm_plan(state, text, capabilities)
    # A provider can return a schema-valid clarification even though the
    # current working state already resolves the request (or the escalation
    # threshold has been reached). Treat this as a recoverable planning miss
    # and prefer the current-turn deterministic state transition.
    if (
        llm_output.next_action.type == "ASK_USER"
        and llm_output.reason_code in {"PRODUCT_REQUIRED", "INTENT_UNCLEAR", "CLARIFICATION_REQUIRED"}
    ):
        recovered = _deterministic_plan(state, text)
        if recovered and recovered.next_action.type in {"ASK_USER", "ASK_CONFIRMATION", "TOOL_CALL"}:
            return recovered
    if llm_output.reason_code not in {"LLM_OUTPUT_INVALID", "INTENT_UNCLEAR"}:
        return llm_output
    # Provider/schema failure is an internal contract failure, not proof that
    # the customer's turn is ambiguous. Re-plan from the current turn and the
    # already-resolved state only; never replay a previous tool plan.
    recovered = _deterministic_plan(state, text)
    if recovered and recovered.next_action.type in {"ASK_USER", "ASK_CONFIRMATION", "TOOL_CALL"}:
        return recovered
    return llm_output
