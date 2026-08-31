from typing import Any

from .multi_agent_contracts import AgentTask, ComplaintContext
from .state import CustomerServiceState
from ..domain.claims_service import create_complaint


class AfterSalesAgent:
    def intake(self, task: AgentTask, state: CustomerServiceState) -> dict[str, Any]:
        if task.target_agent != "AFTER_SALES":
            return {"ok": False, "reason_code": "WRONG_AGENT"}
        return {"ok": True, "task_id": task.id, "current_order": state.current_order}

    def classify(self, text: str, order_id: str | None = None) -> ComplaintContext:
        if any(word in text for word in ("错发", "发错")):
            issue_type = "WRONG_ITEM"
        elif any(word in text for word in ("漏发", "少了")):
            issue_type = "MISSING_ITEM"
        elif any(word in text for word in ("破损", "压坏")):
            issue_type = "DAMAGED_PRODUCT"
        else:
            issue_type = "OTHER"
        return ComplaintContext(issue_type=issue_type, customer_claim=text, order_id=order_id)

    def start_case(self, text: str, order_id: str | None = None) -> dict[str, Any]:
        context = self.classify(text, order_id)
        return create_complaint(context.issue_type, text, order_id)
