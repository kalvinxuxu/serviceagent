from __future__ import annotations

import asyncio
import json
import os
import re
import threading
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from ..llm import get_provider
from .contracts import UnderstandingOutput, RequestedItem
from .state import CustomerServiceState, Message
from .intent_canonicalizer import canonicalize_goal


class SemanticTarget(BaseModel):
    model_config = ConfigDict(extra="ignore")
    type: Literal["PRODUCT", "REFERENCE", "CATEGORY", "MULTIPLE", "NONE"] = "NONE"
    value: str | list[str] | None = None


class SemanticWorkspaceOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    intent: str = "OTHER"
    target: SemanticTarget = Field(default_factory=SemanticTarget)
    operation: Literal["SELECT", "ADD", "REMOVE", "SET_QUANTITY", "REPLACE", "KEEP", "REQUOTE", "ASK_INFORMATION", "CORRECT"] = "ASK_INFORMATION"
    quantity: int | None = Field(default=None, ge=1)
    constraints: dict[str, Any] = Field(default_factory=dict)
    context_relation: Literal["CONTINUE", "MODIFY", "NEW_TOPIC", "CORRECTION"] = "CONTINUE"
    confidence: float = Field(default=0, ge=0, le=1)
    followup_intent: Literal["ACCEPT_FOLLOWUP", "REJECT_FOLLOWUP", "CLARIFY_FOLLOWUP", "NONE"] = "NONE"
    items: list[dict[str, Any]] = Field(default_factory=list)


def semantic_action(workspace: SemanticWorkspaceOutput) -> dict[str, Any]:
    """Expose only the semantic action; SKU and business facts stay outside it."""
    return {
        "operation": workspace.operation,
        "target": workspace.target.model_dump(),
        "quantity": workspace.quantity,
        "intent": workspace.intent,
    }


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


def _canonical_intent(value: str) -> str:
    return canonicalize_goal(value) or value.strip().upper().replace(" ", "_") or "OTHER"


def _prompt_context(state: CustomerServiceState, text: str) -> dict[str, Any]:
    return {
        "current_text": text,
        "recent_messages": [message.model_dump() for message in state.messages[-8:]],
        "business_state": {
            "focused_product": state.focused_product,
            "recent_products": state.recent_products,
            "selected_products": state.known_facts.get("selected_products", []),
            "quote_context": state.quote_context.model_dump() if state.quote_context else None,
            "reference_candidates": state.recommendation_candidates,
            "missing_slots": state.missing_slots,
            "pending_followup": state.pending_followup.model_dump() if state.pending_followup else None,
        },
    }


def understand_semantic(state: CustomerServiceState, text: str) -> SemanticWorkspaceOutput:
    if os.getenv("LLM_PROVIDER", "mock").lower() == "mock":
        return _from_legacy_fallback(state, text)
    context = _prompt_context(state, text)
    messages = [
        Message(role="system", content=(
            "你是客服语义工作区，只理解当前用户表达，不选择工具、不生成SKU、不计算价格。"
            "输出JSON：intent、target(type/value)、operation、quantity、constraints、context_relation、confidence。"
            "target.type只能是PRODUCT、REFERENCE、CATEGORY、MULTIPLE、NONE；"
            "operation只能是SELECT、ADD、REMOVE、SET_QUANTITY、REPLACE、KEEP、REQUOTE、ASK_INFORMATION、CORRECT。"
            "把‘最便宜的’表示为REFERENCE/CHEAPEST，把‘第二个’表示为REFERENCE/SECOND，"
            "把‘刚才那个’表示为REFERENCE/FOCUSED。"
            "如果当前用户是在回应上一轮客服建议，使用followup_intent：接受用ACCEPT_FOLLOWUP，拒绝用REJECT_FOLLOWUP。"
        )),
        Message(role="user", content=json.dumps(context, ensure_ascii=False)),
    ]
    try:
        raw = _run(get_provider().structured_generate(messages=messages, output_schema=SemanticWorkspaceOutput))
        raw.intent = _canonical_intent(raw.intent)
        # Keep model shorthand in the semantic world. Values such as
        # "two"/"total_amount" describe quantity or the quote, not products.
        if raw.target.type == "PRODUCT" and isinstance(raw.target.value, str) and raw.target.value.lower() in {
            "two", "three", "one", "total", "total_amount", "price", "amount"
        }:
            raw.target = SemanticTarget(type="NONE")
        if raw.intent == "PRODUCT_SELECTION" and raw.operation == "ASK_INFORMATION":
            raw.operation = "SELECT"
        if raw.intent == "PRICE_CALCULATION" and raw.operation == "ASK_INFORMATION":
            raw.operation = "REQUOTE"
        # The workspace may understand the intent correctly while returning
        # only a partial target for a multi-product utterance.  Enrich the
        # semantic output with catalog-backed mentions from the current turn.
        # This is entity extraction, not SKU generation: the existing
        # Entity Resolver remains the only component allowed to resolve IDs.
        from .understanding import _deterministic_understanding
        catalog_understanding = _deterministic_understanding(text)
        existing_queries = {
            str(item.get("query", "")) for item in raw.items if item.get("query")
        }
        for item in catalog_understanding.requested_items:
            if item.query not in existing_queries:
                raw.items.append({
                    "query": item.query,
                    "quantity": item.quantity,
                    "operation": item.operation,
                })
                existing_queries.add(item.query)
        return raw
    except Exception:
        # Fallback only interprets this turn; historical references remain the
        # responsibility of ReferenceResolver.
        return _from_legacy_fallback(state, text)


def _from_legacy_fallback(state: CustomerServiceState, text: str) -> SemanticWorkspaceOutput:
    from .understanding import _deterministic_understanding
    semantic = _deterministic_understanding(text)
    requested = semantic.requested_items
    if any(word in text for word in ("最便宜", "最贵")) and (state.recommendation_candidates or state.known_facts.get("recommendations")):
        quantity_match = re.search(r"(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个", text)
        numbers = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
        quantity = None if not quantity_match else int(quantity_match.group(1)) if quantity_match.group(1).isdigit() else numbers[quantity_match.group(1)]
        return SemanticWorkspaceOutput(
            intent="PRODUCT_SELECTION" if quantity else "PRODUCT_COMPARE",
            target=SemanticTarget(type="REFERENCE", value="CHEAPEST" if "最便宜" in text else "MOST_EXPENSIVE"),
            operation="SELECT" if quantity else "ASK_INFORMATION", quantity=quantity, confidence=0.95,
        )
    if requested:
        if len(requested) > 1:
            return SemanticWorkspaceOutput(
                intent="PRICE_CALCULATION", target=SemanticTarget(type="MULTIPLE", value=[item.query for item in requested]),
                operation="ADD", quantity=None, items=[{"query": item.query, "quantity": item.quantity} for item in requested],
                constraints=semantic.constraints, confidence=1.0,
            )
        item = requested[0]
        target_type = "CATEGORY" if item.category and item.category == item.query else "PRODUCT"
        return SemanticWorkspaceOutput(
            intent="PRICE_CALCULATION" if "PRICE_CALCULATION" in semantic.goals else "INVENTORY_CHECK" if "INVENTORY_CHECK" in semantic.goals else "SELECT_PRODUCT",
            target=SemanticTarget(type=target_type, value=item.query), operation="ADD" if item.operation == "ADD" else item.operation,
            quantity=item.quantity, constraints=semantic.constraints, confidence=1.0,
        )
    quantity_match = re.search(r"(\d+|一|两|二|三|四|五|六|七|八|九|十)\s*个", text)
    if quantity_match and (state.focused_product or state.known_facts.get("selected_products")):
        numbers = {"一": 1, "两": 2, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
        raw = quantity_match.group(1)
        return SemanticWorkspaceOutput(
            intent="SELECT_PRODUCT", target=SemanticTarget(type="REFERENCE", value="FOCUSED"),
            operation="SET_QUANTITY" if any(word in text for word in ("改成", "调整为", "变成")) else "SELECT",
            quantity=int(raw) if raw.isdigit() else numbers[raw], confidence=0.9,
        )
    return SemanticWorkspaceOutput(
        intent=semantic.goals[0] if semantic.goals else "OTHER",
        target=SemanticTarget(type="NONE"), operation="REQUOTE" if any(word in text for word in ("一共", "多少钱", "总价")) else "ASK_INFORMATION",
        constraints=semantic.constraints, confidence=0.8,
    )


def to_understanding(semantic: SemanticWorkspaceOutput) -> UnderstandingOutput:
    goal = _canonical_intent(semantic.intent)
    goals = [goal] if goal in {"INVENTORY_CHECK", "PRICE_CALCULATION", "PRODUCT_BROWSE", "PRODUCT_COMPARE", "PRODUCT_RECOMMENDATION", "PRODUCT_FIT_QUERY", "SHIPPING_POLICY", "PROMOTION_QUERY", "MEMBERSHIP_PRICING", "FAQ", "RESERVATION", "RETURN", "ORDER_STATUS", "AFTER_SALES"} else []
    references = []
    if semantic.target.type == "REFERENCE" and semantic.target.value:
        references = [str(semantic.target.value)]
    requested = []
    if semantic.items:
        requested = [RequestedItem(query=str(item.get("query", "")), quantity=int(item.get("quantity", 1)), operation="ADD") for item in semantic.items if item.get("query")]
    elif semantic.target.type == "MULTIPLE" and isinstance(semantic.target.value, list):
        requested = [RequestedItem(query=str(value), quantity=semantic.quantity or 1, operation="ADD") for value in semantic.target.value]
    elif semantic.target.type in {"PRODUCT", "CATEGORY"} and isinstance(semantic.target.value, str) and semantic.target.value:
        operation = "ADD" if semantic.operation == "SELECT" else semantic.operation if semantic.operation in {"ADD", "REMOVE", "SET_QUANTITY", "REPLACE", "KEEP"} else "ADD"
        requested = [RequestedItem(
            query=semantic.target.value,
            quantity=semantic.quantity or 1,
            operation=operation,
            category=semantic.target.value if semantic.target.type == "CATEGORY" else None,
        )]
    return UnderstandingOutput(
        goals=goals,
        requested_items=requested,
        references=references,
        constraints=semantic.constraints,
        feedback={"type": semantic.followup_intent} if semantic.followup_intent != "NONE" else None,
        conversation_act="SELECT" if semantic.operation in {"SELECT", "ADD"} else "MODIFY" if semantic.operation in {"REMOVE", "SET_QUANTITY", "REPLACE"} else "FOLLOW_UP",
    )
