from datetime import datetime
from sqlalchemy import select

from .agent.state import CustomerServiceState
from .db.models.service import Conversation, ConversationGoal, ConversationMessage, ConversationState
from .db.session import SessionLocal, init_db


def save_state(state: CustomerServiceState) -> None:
    init_db()
    now = datetime.utcnow()
    with SessionLocal() as db:
        conversation = db.get(Conversation, state.session_id)
        if conversation is None:
            conversation = Conversation(id=state.session_id, customer_id=state.customer_id, owner_customer_id=state.owner_customer_id, status=state.status)
            db.add(conversation)
        conversation.customer_id = state.customer_id
        conversation.owner_customer_id = state.owner_customer_id
        conversation.status = state.status
        conversation.updated_at = now
        checkpoint = db.get(ConversationState, state.session_id)
        if checkpoint is None:
            checkpoint = ConversationState(conversation_id=state.session_id, version=1, state_json=state.model_dump(mode="json"))
            db.add(checkpoint)
        else:
            checkpoint.version += 1
            checkpoint.state_json = state.model_dump(mode="json")
            checkpoint.updated_at = now
        existing_messages = db.query(ConversationMessage).filter_by(conversation_id=state.session_id).count()
        for message in state.messages[existing_messages:]:
            db.add(ConversationMessage(conversation_id=state.session_id, role=message.role, actor_id=message.actor_id, content=str(message.content)))
        for goal in state.goals:
            item = db.get(ConversationGoal, goal["id"])
            if item is None:
                db.add(ConversationGoal(id=goal["id"], conversation_id=state.session_id, goal_type=goal["type"], status=goal["status"], priority=goal.get("priority", 1), goal_json=goal))
            else:
                item.status = goal["status"]
                item.goal_json = goal
                item.updated_at = now
        db.commit()


def load_state(session_id: str) -> CustomerServiceState | None:
    init_db()
    with SessionLocal() as db:
        checkpoint = db.get(ConversationState, session_id)
        return CustomerServiceState.model_validate(checkpoint.state_json) if checkpoint else None


def confirm_order_transaction(session_id: str, actor_id: str) -> CustomerServiceState | None:
    """Atomically confirm one actor's quote against the latest DB checkpoint."""
    from .agent.group_context import activate_customer, persist_active_customer
    init_db()
    with SessionLocal.begin() as db:
        row = db.execute(select(ConversationState).where(ConversationState.conversation_id == session_id).with_for_update()).scalar_one_or_none()
        if row is None:
            return None
        state = CustomerServiceState.model_validate(row.state_json)
        activate_customer(state, actor_id)
        if not state.quote_context or state.known_facts.get("order_id"):
            return state
        state.known_facts["order_confirmation_status"] = "CONFIRMED"
        state.requires_confirmation = False
        state.status = "RESOLVED"
        persist_active_customer(state)
        row.version += 1
        row.state_json = state.model_dump(mode="json")
        row.updated_at = datetime.utcnow()
        conversation = db.get(Conversation, session_id)
        if conversation:
            conversation.customer_id = actor_id
            conversation.status = state.status
            conversation.updated_at = datetime.utcnow()
        return state
