import json
import os

import httpx
from pydantic import ValidationError

from .base import SchemaT


class OpenAICompatibleProvider:
    def __init__(self, *, base_url: str, api_key: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model

    async def structured_generate(self, *, messages, output_schema: type[SchemaT], temperature: float = 0) -> SchemaT:
        timeout_env = "VISION_TIMEOUT_SECONDS" if output_schema.__name__ == "EvidenceObservation" else "LLM_TIMEOUT_SECONDS"
        try:
            timeout_seconds = max(float(os.getenv(timeout_env, "60" if timeout_env == "VISION_TIMEOUT_SECONDS" else "10")), 1.0)
        except ValueError:
            timeout_seconds = 60.0 if timeout_env == "VISION_TIMEOUT_SECONDS" else 10.0
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": [{"role": item.role, "content": item.content} for item in messages],
            # DeepSeek's current OpenAI-compatible API supports json_object;
            # Pydantic performs the strict schema validation after parsing.
            "response_format": {"type": "json_object"},
            "max_tokens": 1200,
        }
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        raw = json.loads(content)
        try:
            return output_schema.model_validate(raw)
        except Exception:
            if output_schema.__name__ == "SemanticWorkspaceOutput":
                # Providers often return semantically valid shorthand (for
                # example target="芝士贝果" or operation="check_availability").
                # Normalize the contract boundary; do not resolve products or
                # choose business capabilities here.
                target = raw.get("target")
                if isinstance(target, str):
                    target = {"type": "PRODUCT", "value": target}
                elif not isinstance(target, dict):
                    target = {"type": "NONE", "value": None}
                target_type = str(target.get("type") or "NONE").upper()
                type_aliases = {"ITEM": "PRODUCT", "PRODUCT_NAME": "PRODUCT", "REF": "REFERENCE", "CLASS": "CATEGORY"}
                target["type"] = type_aliases.get(target_type, target_type if target_type in {"PRODUCT", "REFERENCE", "CATEGORY", "MULTIPLE", "NONE"} else "NONE")
                operation = str(raw.get("operation") or raw.get("action") or "ASK_INFORMATION").upper()
                operation_aliases = {
                    "CHECK_AVAILABILITY": "ASK_INFORMATION", "CHECK_INVENTORY": "ASK_INFORMATION",
                    "SELECT_PRODUCT": "SELECT", "ADD_ITEM": "ADD", "UPDATE_QUANTITY": "SET_QUANTITY",
                    "CALCULATE_PRICE": "REQUOTE", "QUOTE": "REQUOTE", "ASK_PRICE": "REQUOTE",
                }
                operation = operation_aliases.get(operation, operation)
                if operation not in {"SELECT", "ADD", "REMOVE", "SET_QUANTITY", "REPLACE", "KEEP", "REQUOTE", "ASK_INFORMATION", "CORRECT"}:
                    operation = "ASK_INFORMATION"
                relation = str(raw.get("context_relation") or "CONTINUE").upper()
                relation_aliases = {"NONE": "CONTINUE", "SAME": "CONTINUE", "FOLLOW_UP": "CONTINUE", "UPDATE": "MODIFY", "SWITCH": "NEW_TOPIC"}
                relation = relation_aliases.get(relation, relation)
                if relation not in {"CONTINUE", "MODIFY", "NEW_TOPIC", "CORRECTION"}:
                    relation = "CONTINUE"
                normalized = dict(raw)
                normalized.update({"target": target, "operation": operation, "context_relation": relation})
                target_model = output_schema.model_fields["target"].annotation
                target_value = target_model.model_validate(target) if hasattr(target_model, "model_validate") else target
                quantity = normalized.get("quantity")
                try:
                    quantity = int(quantity) if quantity is not None else None
                    quantity = quantity if quantity and quantity > 0 else None
                except (TypeError, ValueError):
                    quantity = None
                try:
                    confidence = min(max(float(normalized.get("confidence", 0)), 0.0), 1.0)
                except (TypeError, ValueError):
                    confidence = 0.0
                # Construct after normalization so a provider's harmless extra
                # fields or scalar shorthand cannot invalidate the whole turn.
                return output_schema.model_construct(**{
                    "intent": str(normalized.get("intent") or "OTHER"), "target": target_value,
                    "operation": operation, "quantity": quantity,
                    "constraints": normalized.get("constraints") if isinstance(normalized.get("constraints"), dict) else {},
                    "context_relation": relation, "confidence": confidence,
                })
            if output_schema.__name__ == "EvidenceObservation":
                def normalize_confidence(value):
                    try:
                        return min(max(float(value), 0.0), 1.0)
                    except (TypeError, ValueError):
                        return 0.0

                def normalize_scalar(value):
                    if value is None or isinstance(value, (str, int, float, bool)):
                        return value
                    if isinstance(value, list):
                        value = next((item for item in value if item), None)
                        return normalize_scalar(value)
                    return str(value) if value else None

                facts = raw.get("observed_facts") or raw.get("observed_elements") or []
                if isinstance(facts, str):
                    facts = [facts]
                elif isinstance(facts, dict):
                    facts = [f"{key}：{value}" for key, value in facts.items()]
                elif not isinstance(facts, list):
                    facts = [facts]
                uncertainties = raw.get("uncertainties") or raw.get("unknowns") or []
                if isinstance(uncertainties, str):
                    uncertainties = [uncertainties]
                elif isinstance(uncertainties, dict):
                    uncertainties = [f"{key}：{value}" for key, value in uncertainties.items()]
                elif not isinstance(uncertainties, list):
                    uncertainties = [uncertainties]
                normalized = {
                    "source": "IMAGE",
                    "classification": str(raw.get("classification") or raw.get("category") or "UNCLASSIFIED"),
                    "confidence": normalize_confidence(raw.get("confidence") or raw.get("score")),
                    "address_candidate": normalize_scalar(raw.get("address_candidate") or raw.get("address") or raw.get("extracted_address")),
                    "order_id_candidate": normalize_scalar(raw.get("order_id_candidate") or raw.get("order_id") or raw.get("order_number")),
                    "tracking_number_candidate": normalize_scalar(raw.get("tracking_number_candidate") or raw.get("tracking_number") or raw.get("waybill_number")),
                    "carrier": normalize_scalar(raw.get("carrier")),
                    "observed_facts": [str(item) for item in facts],
                    "uncertainties": [str(item) for item in uncertainties],
                    "observed_at": str(normalize_scalar(raw.get("observed_at")) or "runtime"),
                    "side_effect_allowed": False,
                }
                try:
                    return output_schema.model_validate(normalized)
                except ValidationError:
                    return output_schema.model_construct(**normalized)
            if output_schema.__name__ == "UnderstandingOutput" or "requested_items" in getattr(output_schema, "model_fields", {}):
                allowed_operations = {"ADD", "REMOVE", "SET_QUANTITY", "REPLACE", "KEEP"}

                def normalize_quantity(value):
                    try:
                        value = int(value)
                        return value if value > 0 else 1
                    except (TypeError, ValueError):
                        return 1

                def normalize_list(value):
                    return value if isinstance(value, list) else []

                mentions = []
                for item in raw.get("product_mentions", []):
                    if isinstance(item, dict):
                        mentions.append({
                            "text": item.get("text") or item.get("mention_text") or item.get("product_query", ""),
                            "product_query": item.get("product_query") or item.get("text") or item.get("mention_text", ""),
                        })
                requested_items = []
                for item in raw.get("requested_items") or raw.get("order_items") or []:
                    if isinstance(item, dict):
                        operation = item.get("operation") if item.get("operation") in allowed_operations else "ADD"
                        attributes = item.get("attributes")
                        if isinstance(attributes, dict):
                            attributes = list(attributes.keys())
                        if not isinstance(attributes, list):
                            attributes = []
                        requested_items.append({
                            "query": item.get("query") or item.get("name") or item.get("text") or "",
                            "quantity": normalize_quantity(item.get("quantity")),
                            "operation": operation,
                            "attributes": [str(attribute) for attribute in attributes],
                            "category": item.get("category") if isinstance(item.get("category"), str) else None,
                        })
                operations = []
                for item in raw.get("conversation_operations") or raw.get("operations") or []:
                    if isinstance(item, dict) and item.get("operation") and (item.get("target") or item.get("query") or item.get("name")):
                        operations.append({
                            "operation": item["operation"],
                            "target": item.get("target") or item.get("query") or item.get("name"),
                            "quantity": item.get("quantity"),
                            "replacement": item.get("replacement"),
                        })
                goal_from_decision = raw.get("goal_type") or raw.get("intent") or raw.get("user_intent")
                normalized_goals = normalize_list(raw.get("goals") or raw.get("candidate_goals") or raw.get("candidate_goals_list"))
                if not normalized_goals and goal_from_decision:
                    normalized_goals = [str(goal_from_decision)]
                normalized = {
                    "goals": normalized_goals,
                    "candidate_goals": normalize_list(raw.get("candidate_goals") or normalized_goals),
                    "requested_items": requested_items,
                    "conversation_operations": operations,
                    "product_mentions": mentions,
                    "order_references": normalize_list(raw.get("order_references") or raw.get("order_ids")),
                    "constraints": raw.get("constraints") if isinstance(raw.get("constraints"), dict) else {},
                    "references": normalize_list(raw.get("references") or raw.get("contextual_references")),
                    "requires_clarification": bool(raw.get("requires_clarification", False)),
                    "conversation_act": raw.get("conversation_act") or ("SELECT" if str(raw.get("action_type", "")).upper() in {"TOOL_CALL", "RESPOND"} and raw.get("tool_name") else "REQUEST"),
                }
                return output_schema.model_validate(normalized)
            # Some compatible endpoints return a semantically equivalent
            # clarification envelope; normalize it, then validate again.
            if "requested_items" in getattr(output_schema, "model_fields", {}):
                goal_value = raw.get("goal_type") or raw.get("intent") or raw.get("user_intent")
                goals = raw.get("goals") or raw.get("candidate_goals") or ([goal_value] if goal_value else [])
                return output_schema.model_construct(
                    goals=goals if isinstance(goals, list) else [str(goals)],
                    candidate_goals=goals if isinstance(goals, list) else [str(goals)],
                    requested_items=[], conversation_operations=[], product_mentions=[],
                    order_references=[], constraints={}, references=[], requires_clarification=False,
                    semantic_state={}, constraint_updates={}, feedback=None, memory_candidate=None,
                    conversation_act="REQUEST", slot_values={}, delivery_intent=False, delivery_mode="UNKNOWN",
                )
            decision_label = str(raw.get("decision") or raw.get("action") or "").lower()
            if "clarif" in decision_label or "ask" in decision_label:
                return output_schema.model_validate({
                    "current_goal_id": "goal_unknown",
                    "action_type": "ASK_USER",
                    "tool_name": None,
                    "tool_args": {},
                    "message": raw.get("text") or raw.get("message") or "请补充你的需求。",
                    "missing_fields": ["goal"],
                    "reason_code": "INTENT_UNCLEAR",
                    "expected_state_transition": "WAITING_USER",
                })
            raise
