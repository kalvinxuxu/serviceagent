from .base import SchemaT


class MockProvider:
    """Deterministic provider used by tests and local development."""

    async def structured_generate(self, *, messages, output_schema: type[SchemaT], temperature: float = 0) -> SchemaT:
        text = messages[-1].content if messages else ""
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
