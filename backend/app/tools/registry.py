from datetime import datetime, timezone
from ..agent.contracts import ToolResult
from ..domain import catalog, return_service
from .recommendation_tools import recommend_products, recommendation_metadata
from ..domain.pricing_service import calculate_order_quote, calculate_total
from ..domain.inventory_service import check_items, list_available
from ..domain.reservation_service import reserve_product
from ..domain.comparison_service import compare_products
from ..domain.business_config import SALES_POLICY
from ..domain.store_faq_service import answer as answer_store_faq
from ..domain.product_fit_service import explain_product_fit
from ..agent.evidence_service import match_order, simulated_logistics

def _now(): return datetime.now(timezone.utc).isoformat()

def execute(tool_name: str, arguments: dict) -> ToolResult:
    try:
        if tool_name == "search_products":
            data = catalog.search_products(arguments.get("query", ""), arguments.get("tags"))
        elif tool_name == "recommend_products":
            data = recommend_products(**arguments)
        elif tool_name == "recommendation_metadata":
            data = recommendation_metadata(arguments.get("constraints"))
        elif tool_name == "compare_products":
            result = compare_products(arguments.get("product_ids"), arguments.get("category"))
            return ToolResult(observed_at=_now(), **result)
        elif tool_name == "get_sales_policy":
            return ToolResult(ok=True, data=SALES_POLICY, observed_at=_now())
        elif tool_name == "answer_store_faq":
            return ToolResult(ok=True, data=answer_store_faq(arguments.get("question", "")), observed_at=_now())
        elif tool_name == "explain_product_fit":
            result = explain_product_fit(arguments["product_id"], arguments.get("audience"), arguments.get("concern"))
            return ToolResult(ok=result.get("ok", False), data=result if result.get("ok", False) else None, reason=result.get("reason"), observed_at=_now())
        elif tool_name == "calculate_total":
            result = calculate_total(arguments.get("items", []))
            return ToolResult(observed_at=_now(), **result)
        elif tool_name == "calculate_order_quote":
            result = calculate_order_quote(arguments.get("items", []), arguments.get("discount", 0), arguments.get("shipping"), arguments.get("customer_type", "REGULAR"), arguments.get("delivery_mode", "PICKUP"))
            return ToolResult(observed_at=_now(), **result)
        elif tool_name == "check_inventory":
            result = catalog.check_inventory(arguments["product_id"])
            return ToolResult(**result)
        elif tool_name == "list_available_inventory":
            result = list_available(arguments.get("category"), arguments.get("query", ""), arguments.get("max_results", 20))
            return ToolResult(**result)
        elif tool_name == "check_selected_items_inventory":
            result = check_items(arguments.get("items", []))
            return ToolResult(**result)
        elif tool_name == "reserve_product":
            result = reserve_product(**arguments)
            return ToolResult(**result)
        elif tool_name == "edit_selected_items":
            return ToolResult(ok=True, data={"items": arguments.get("items", [])}, observed_at=_now())
        elif tool_name == "match_order_from_evidence":
            return ToolResult(ok=True, data=match_order(arguments.get("evidence", {}), arguments.get("customer_id")), observed_at=_now())
        elif tool_name == "query_logistics_status":
            result = simulated_logistics(arguments["order_id"])
            return ToolResult(observed_at=_now(), **result)
        elif tool_name in {"create_delivery_request", "submit_delivery_request", "create_order"}:
            slots = arguments.get("delivery_slots", {})
            required = ("delivery_address", "recipient_name", "phone")
            missing = [name for name in required if not slots.get(name)]
            if missing:
                return ToolResult(ok=False, reason=f"DELIVERY_SLOT_REQUIRED:{missing[0]}", observed_at=_now())
            if not arguments.get("confirmed"):
                return ToolResult(ok=False, reason="DELIVERY_CONFIRMATION_REQUIRED", observed_at=_now())
            return ToolResult(ok=True, data={"status": "SIMULATED_ACCEPTED", "recipient_name": slots["recipient_name"]}, observed_at=_now())
        elif tool_name == "find_recent_orders":
            data = catalog.find_recent_orders(arguments["customer_id"])
        elif tool_name == "get_order":
            data = catalog.get_order(arguments["order_id"])
            if data is None: return ToolResult(ok=False, reason="ORDER_NOT_FOUND", observed_at=_now())
        elif tool_name == "check_return_eligibility":
            data = return_service.check_return_eligibility(arguments["order_id"], arguments["customer_id"])
        elif tool_name == "create_return_request":
            result = return_service.create_return_request(arguments["order_id"], arguments["customer_id"], arguments.get("confirmed", False))
            return ToolResult(observed_at=_now(), **result)
        else:
            return ToolResult(ok=False, reason="TOOL_NOT_ALLOWED", observed_at=_now())
        return ToolResult(ok=True, data=data, observed_at=_now())
    except (KeyError, TypeError) as exc:
        return ToolResult(ok=False, reason=f"INVALID_ARGUMENTS:{exc}", observed_at=_now())
