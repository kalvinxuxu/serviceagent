import json
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from uuid import uuid4
from ..agent.state import CustomerServiceState
from ..agent.graph import run_turn
from ..core.logging import configure_logging
from ..conversation_service import load_state, save_state
from ..agent.goal_stack import update_goal_status
from ..agent.evidence_service import observe_attachment, save_attachment, match_order
from ..domain.handoff_service import create_handoff
from ..agent.slot_manager import next_clarification
from ..agent.group_context import activate_customer, persist_active_customer, summaries_for_members

configure_logging()

router = APIRouter(prefix="/api/v1")
SESSIONS: dict[str, CustomerServiceState] = {}


def build_order_summary(state: CustomerServiceState) -> dict:
    quote = state.quote_context.model_dump() if state.quote_context else {}
    items = quote.get("items") or state.known_facts.get("selected_products", [])
    delivery_mode = quote.get("delivery_mode") or state.delivery_mode
    delivery_complete = delivery_mode == "PICKUP" or all(state.delivery_slots.get(slot) for slot in ("delivery_address", "recipient_name", "phone"))
    confirmed = state.known_facts.get("order_confirmation_status") == "CONFIRMED"
    return {
        "customer_id": state.customer_id,
        "items": items,
        "subtotal": quote.get("subtotal", 0),
        "discount": quote.get("discount", 0),
        "shipping": quote.get("shipping", 0),
        "total": quote.get("total", 0),
        "delivery_mode": delivery_mode,
        "status": "CONFIRMED" if confirmed else state.status,
        "requires_confirmation": bool(items) and delivery_complete and not confirmed,
    }

class CreateSession(BaseModel):
    customer_id: str | None = "CUS001"
    group_member_ids: list[str] = Field(default_factory=list)
    owner_customer_id: str | None = None

class MessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    customer_id: str | None = None
    actor_id: str | None = None
    confirmed: bool = False


class GoalControlRequest(BaseModel):
    reason: str | None = None

@router.post("/sessions")
def create_session(req: CreateSession = CreateSession()):
    sid = f"ses_{uuid4().hex[:8]}"
    members = req.group_member_ids or ([req.customer_id] if req.customer_id else [])
    owner = req.owner_customer_id or req.customer_id
    SESSIONS[sid] = CustomerServiceState(session_id=sid, customer_id=req.customer_id, owner_customer_id=owner, active_customer_id=req.customer_id, group_member_ids=members)
    save_state(SESSIONS[sid])
    return {"session_id": sid, "status": SESSIONS[sid].status}

def _is_confirmation(text: str) -> bool:
    return text.strip() in {"是", "对", "对的", "正确", "没错", "确认", "是的", "可以"}


def _session_state(session_id: str) -> CustomerServiceState | None:
    # The database is authoritative. The in-process map is only a compatibility
    # fallback for legacy tests that inject a state directly.
    return load_state(session_id) or SESSIONS.get(session_id)


def _authorize_actor(state: CustomerServiceState, actor_id: str | None, owner_id: str | None) -> str:
    actor = str(actor_id or state.customer_id or "CUS001")
    if state.owner_customer_id and len(state.group_member_ids) > 1 and owner_id != state.owner_customer_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="SESSION_OWNER_MISMATCH")
    if state.group_member_ids and actor not in state.group_member_ids:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="ACTOR_NOT_IN_SESSION")
    if not state.group_member_ids and state.customer_id and actor != state.customer_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="ACTOR_NOT_IN_SESSION")
    return actor


def _evidence_response(state: CustomerServiceState, reply: str, trace: dict | None = None):
    persist_active_customer(state)
    summaries = summaries_for_members(state, build_order_summary)
    save_state(state)
    return {"session_id": state.session_id, "actor_id": state.active_customer_id, "message": {"role": "assistant", "content": reply, "actor_id": state.active_customer_id}, "attachments": state.known_facts.get("response_attachments", []), "handoff_offer": bool(state.known_facts.get("handoff_offer")), "status": state.status, "requires_confirmation": state.requires_confirmation, "requires_human": state.requires_human, "order_summary": summaries[state.active_customer_id] if state.active_customer_id else build_order_summary(state), "order_summaries": summaries, "inspector": trace or {}}


@router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, request: Request):
    state = _session_state(session_id)
    if state is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    SESSIONS[session_id] = state
    content_type = request.headers.get("content-type", "")
    if content_type.startswith("multipart/form-data") or content_type.startswith("application/x-www-form-urlencoded"):
        form = await request.form()
        message = str(form.get("message") or "").strip()
        customer_id = form.get("actor_id") or form.get("customer_id")
        confirmed = str(form.get("confirmed") or "false").lower() == "true"
        uploads = [item for item in form.multi_items() if item[0] == "attachments"]
    else:
        try:
            payload = await request.json()
        except ValueError:
            # Some clients send a body without a reliable content-type; parse
            # it as a form before returning a generic service failure.
            form = await request.form()
            message = str(form.get("message") or "").strip()
            customer_id = form.get("actor_id") or form.get("customer_id")
            confirmed = str(form.get("confirmed") or "false").lower() == "true"
            uploads = [item for item in form.multi_items() if item[0] == "attachments"]
            payload = None
        if payload is None:
            req = None
        else:
            req = MessageRequest.model_validate(payload)
        if req is not None:
            message, customer_id, confirmed, uploads = req.message, req.actor_id or req.customer_id, req.confirmed, []
    actor_id = _authorize_actor(state, customer_id, request.headers.get("x-session-owner"))
    activate_customer(state, actor_id)

    if state.pending_evidence and message and _is_confirmation(message):
        pending = state.pending_evidence
        if pending.get("classification") == "ADDRESS" and pending.get("address_candidate"):
            state.delivery_slots["delivery_address"] = pending["address_candidate"]
            state.pending_evidence = None
            state.requires_confirmation = False
            state.evidence_history.append({"evidence_id": pending.get("evidence_id"), "status": "COMMITTED", "classification": "ADDRESS"})
            if not state.quote_context and not state.known_facts.get("selected_products"):
                state.status = "WAITING_USER"
                return _evidence_response(state, "地址已确认。广东省内支持顺丰寄送，运费按实际规则计算；如果您要下单寄送，我再为您收集收货人和联系电话。", {"reason_code": "EVIDENCE_COMMITTED", "evidence_id": pending.get("evidence_id")})
            clarification = next_clarification("CREATE_DELIVERY_REQUEST", state.delivery_slots)
            state.status = "WAITING_USER"
            return _evidence_response(state, clarification.missing_slots[0].prompt if clarification else "地址已确认。", {"reason_code": "EVIDENCE_COMMITTED", "evidence_id": pending.get("evidence_id")})
        if pending.get("classification") in {"ORDER_REFERENCE", "TRACKING_REFERENCE"}:
            match = match_order(pending, state.customer_id)
            if match.get("authorized"):
                result = execute("query_logistics_status", {"order_id": match["order_id"]}).model_dump()
                state.pending_evidence = None
                state.logistics_context = result.get("data") if result.get("ok") else None
                return _evidence_response(state, _logistics_reply(result), {"reason_code": "LOGISTICS_QUERY", "evidence_id": pending.get("evidence_id")})

    for _, upload in uploads:
        content = await upload.read()
        attachment = save_attachment(state.session_id, upload.filename or "image", upload.content_type or "", content)
        observation = observe_attachment(attachment)
        state.evidence_history.append({**{key: value for key, value in observation.items() if key not in {"address_candidate"}}, "status": "OBSERVED"})
        classification = observation.get("classification")
        if classification in {"PACKAGING_DAMAGE", "PRODUCT_DAMAGE", "QUALITY_DEFECT", "FOOD_SAFETY_RISK", "DAMAGED_PRODUCT", "QUALITY_RISK"}:
            state.requires_human = True
            state.status = "HANDOFF"
            create_handoff(state, "IMAGE_QUALITY_ISSUE")
            return _evidence_response(state, "我已收到这张图片。为了确保处理准确，我先为您转接人工客服，并保留图片和当前对话。", {"reason_code": "IMAGE_QUALITY_HANDOFF", "evidence_id": observation.get("evidence_id")})
        if classification == "ADDRESS" and observation.get("address_candidate"):
            state.pending_evidence = {**observation, "status": "WAITING_CONFIRMATION"}
            state.status = "WAITING_CONFIRMATION"
            state.requires_confirmation = True
            return _evidence_response(state, f"我从图片中识别到收货地址为：{observation['address_candidate']}。请确认地址是否正确？", {"reason_code": "EVIDENCE_CONFIRMATION_REQUIRED", "evidence_id": observation.get("evidence_id")})
        if classification in {"ORDER_REFERENCE", "TRACKING_REFERENCE"}:
            match = match_order(observation, state.customer_id)
            if match.get("authorized"):
                result = execute("query_logistics_status", {"order_id": match["order_id"]}).model_dump()
                state.logistics_context = result.get("data") if result.get("ok") else None
                return _evidence_response(state, _logistics_reply(result), {"reason_code": "LOGISTICS_QUERY", "evidence_id": observation.get("evidence_id")})
            state.pending_evidence = {**observation, **match, "status": "WAITING_CONFIRMATION"}
            state.status = "WAITING_CONFIRMATION"
            if match.get("match_status") == "MATCHED" and not match.get("authorized"):
                reply = "我识别到了一个订单号，但无法确认它属于当前账户。为了保护您的信息，我不能直接展示订单详情，请提供当前账户下的订单信息。"
            else:
                reply = "我识别到了快递单号，但暂时无法唯一匹配店内订单。请确认单号是否完整，或补充下单账户信息。"
            return _evidence_response(state, reply, {"reason_code": "ORDER_MATCH_OR_AUTHORIZATION_REQUIRED", "evidence_id": observation.get("evidence_id")})
        return _evidence_response(state, "我看到了您上传的图片，但暂时无法可靠识别其中的地址或订单信息。您可以补充文字说明，我再继续帮您处理。", {"reason_code": "IMAGE_UNCLASSIFIED", "evidence_id": observation.get("evidence_id")})

    state, reply, trace = run_turn(state, message, confirmed)
    persist_active_customer(state)
    summaries = summaries_for_members(state, build_order_summary)
    save_state(state)
    return {"session_id": session_id, "actor_id": state.active_customer_id, "message": {"role":"assistant", "content":reply, "actor_id": state.active_customer_id}, "attachments": state.known_facts.get("response_attachments", []), "handoff_offer": bool(state.known_facts.get("handoff_offer")), "status":state.status, "requires_confirmation":state.requires_confirmation, "requires_human":state.requires_human, "order_summary": summaries[state.active_customer_id] if state.active_customer_id else build_order_summary(state), "order_summaries": summaries, "inspector":trace}


def _logistics_reply(result: dict) -> str:
    if not result.get("ok"):
        return "暂时无法查询到物流状态，我先为您转接人工客服处理。"
    data = result["data"]
    latest = data.get("latest_event", {}).get("description")
    return f"我查到您的包裹目前{data.get('status_text', '状态未知')}。" + (f"最新物流记录：{latest}。" if latest else "")

@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    state = _session_state(session_id)
    if state is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    SESSIONS[session_id] = state
    return state.model_dump()


@router.post("/sessions/{session_id}/goals/pause")
def pause_goal(session_id: str, req: GoalControlRequest = GoalControlRequest()):
    state = SESSIONS[session_id]
    state.known_facts["goal_paused"] = True
    state.known_facts["pause_reason"] = req.reason
    state.status = "WAITING_USER"
    update_goal_status(state, "PAUSED")
    save_state(state)
    return {"session_id": session_id, "status": state.status, "goal_paused": True}


@router.post("/sessions/{session_id}/goals/resume")
def resume_goal(session_id: str):
    state = SESSIONS[session_id]
    state.known_facts["goal_paused"] = False
    state.status = "IN_PROGRESS"
    for goal in state.goals:
        if goal["status"] == "PAUSED":
            goal["status"] = "ACTIVE"
    save_state(state)
    return {"session_id": session_id, "status": state.status, "goal_paused": False}


@router.post("/sessions/{session_id}/goals/end")
def end_goal(session_id: str, req: GoalControlRequest = GoalControlRequest()):
    state = SESSIONS[session_id]
    state.known_facts["goal_ended"] = True
    state.known_facts["end_reason"] = req.reason
    state.status = "RESOLVED"
    state.pending_items = []
    update_goal_status(state, "ABANDONED")
    save_state(state)
    return {"session_id": session_id, "status": state.status, "goal_ended": True}
