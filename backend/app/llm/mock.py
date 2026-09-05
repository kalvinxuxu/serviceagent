import json

from .base import SchemaT


class MockProvider:
    """Deterministic provider used by tests and local development."""

    async def structured_generate(self, *, messages, output_schema: type[SchemaT], temperature: float = 0) -> SchemaT:
        text = messages[-1].content if messages else ""
        if output_schema.__name__ == "LLMGenerationOutput":
            return output_schema.model_validate({
                "schema_version": "pqg.v1",
                "questions": [
                    {"text": "需要我再介绍一下适合您的商品吗？", "reason": "商品选择"},
                    {"text": "您还想了解保存方式或配送安排吗？", "reason": "购买决策"},
                ],
            })
        if output_schema.__name__ == "UnderstandingOutput":
            from ..agent.understanding import _deterministic_understanding
            try:
                payload = json.loads(text)
                text = str(payload.get("user_message", text))
            except (TypeError, ValueError):
                pass
            return _deterministic_understanding(text)
        if output_schema.__name__ == "SemanticWorkspaceOutput":
            from ..agent.semantic_workspace import _from_legacy_fallback
            from ..agent.state import CustomerServiceState
            try:
                payload = json.loads(text)
                current_text = str(payload.get("current_text", text))
                business_state = payload.get("business_state", {})
                state = CustomerServiceState(session_id="mock-fallback")
                state.focused_product = business_state.get("focused_product")
                state.recent_products = business_state.get("recent_products", [])
                state.recommendation_candidates = business_state.get("reference_candidates", [])
                state.known_facts["selected_products"] = business_state.get("selected_products", [])
            except (TypeError, ValueError):
                current_text = text
                state = CustomerServiceState(session_id="mock-fallback")
            return _from_legacy_fallback(state, current_text)
        if output_schema.__name__ in {"SupervisorDecision", "Supervisor"}:
            from ..agent.supervisor_router import build_tasks, route_action
            try:
                payload = json.loads(text)
                user_text = str(payload.get("user_message", ""))
                understanding = payload.get("understanding", {})
            except (TypeError, ValueError):
                user_text, understanding = text, {}
            goals = understanding.get("goals") or understanding.get("candidate_goals") or ["OTHER"]
            tasks = build_tasks(goals)
            action = route_action(goals, user_text)
            domain = "AFTER_SALES" if any(t.target_agent == "AFTER_SALES" for t in tasks) and not any(t.target_agent == "COMMERCE" for t in tasks) else "COMMERCE" if tasks else "UNKNOWN"
            return output_schema.model_validate({
                "goals": goals,
                "domain": domain,
                "route_action": action,
                "tasks": tasks,
                "reason_code": "DOMAIN_ROUTE" if tasks else "GOAL_MISSING",
                "confidence": 0.9 if tasks else 0.2,
                "missing_information": [] if tasks else ["goal"],
            })
        if any(word in text for word in ("人工", "客服人员", "赔偿", "法律")):
            action = {"type": "HANDOFF", "message": "我为你转接人工客服，已保留当前对话。"}
            reason = "HUMAN_REQUEST_OR_HIGH_RISK"
        elif any(word in text for word in ("库存", "有货", "还有")):
            action = {"type": "ASK_USER", "message": "请告诉我想查询的商品和规格。"}
            reason = "PRODUCT_REQUIRED"
        else:
            action = {"type": "ASK_USER", "message": "请告诉我具体想咨询的商品、订单或服务。"}
            reason = "INTENT_UNCLEAR"
        return output_schema.model_validate({
            "current_goal_id": "goal_unknown",
            "action_type": action["type"],
            "tool_name": None,
            "tool_args": {},
            "message": action.get("message"),
            "missing_fields": ["goal"],
            "reason_code": reason,
            "expected_state_transition": "WAITING_USER",
        })
