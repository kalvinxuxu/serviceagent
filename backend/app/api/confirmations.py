from fastapi import APIRouter, HTTPException, Header
from .sessions import SESSIONS, build_order_summary, _session_state, _authorize_actor
from ..agent.graph import run_turn
from ..conversation_service import load_state, save_state, confirm_order_transaction
from ..agent.group_context import activate_customer, persist_active_customer, summaries_for_members

router = APIRouter(prefix="/api/v1")

@router.post("/sessions/{session_id}/confirmations")
def confirm(session_id: str, confirmed: bool = True, customer_id: str | None = None, x_session_owner: str | None = Header(default=None)):
    state = _session_state(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    actor_id = _authorize_actor(state, customer_id, x_session_owner)
    activate_customer(state, actor_id)
    if state.quote_context and not state.known_facts.get("order_id"):
        if state.quote_context.delivery_mode == "SHIPPING" and not all(state.delivery_slots.get(slot) for slot in ("delivery_address", "recipient_name", "phone")):
            persist_active_customer(state)
            summaries = summaries_for_members(state, build_order_summary)
            save_state(state)
            return {"session_id": session_id, "status": state.status, "message": "配送信息还未收集完整，请先补充收货地址、收货人和联系电话。", "order_summary": summaries[state.active_customer_id], "order_summaries": summaries, "trace": {"reason_code": "DELIVERY_SLOT_REQUIRED"}}
        if confirmed:
            transaction_state = confirm_order_transaction(session_id, actor_id)
            if transaction_state is not None:
                state = transaction_state
                SESSIONS[session_id] = state
            else:
                state.known_facts["order_confirmation_status"] = "CONFIRMED"
                state.requires_confirmation = False
                state.status = "RESOLVED"
            summaries = summaries_for_members(state, build_order_summary)
            save_state(state)
            return {"session_id": session_id, "status": state.status, "message": "订单已确认，金额和取货方式已记录。", "order_summary": summaries[state.active_customer_id], "order_summaries": summaries, "trace": {"reason_code": "ORDER_CONFIRMATION_ACCEPTED"}}
    SESSIONS[session_id] = state
    state, reply, trace = run_turn(state, "确认", confirmed=confirmed)
    persist_active_customer(state)
    summaries = summaries_for_members(state, build_order_summary)
    save_state(state)
    return {"session_id": session_id, "status": state.status, "message": reply, "order_summary": summaries[state.active_customer_id], "order_summaries": summaries, "trace": trace}
