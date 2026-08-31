from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, Float, DateTime, Text, UniqueConstraint, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..base import Base

class ReturnRequest(Base):
    __tablename__ = "return_requests"
    __table_args__ = (UniqueConstraint("order_item_id", "type", "status", name="uq_return_item_type_status"),)
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"))
    order_item_id: Mapped[str] = mapped_column(String(32))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    type: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(30))
    reason: Mapped[str] = mapped_column(Text, default="")
    refund_amount: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class PolicyArticle(Base):
    __tablename__ = "policy_articles"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    topic: Mapped[str] = mapped_column(String(80))
    content: Mapped[str] = mapped_column(Text)
    version: Mapped[int] = mapped_column(Integer, default=1)


class BusinessConfig(Base):
    __tablename__ = "business_configs"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON, default=dict)
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BusinessConfigAudit(Base):
    __tablename__ = "business_config_audits"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    config_key: Mapped[str] = mapped_column(String(80))
    operation: Mapped[str] = mapped_column(String(30))
    before_value: Mapped[dict] = mapped_column(JSON, default=dict)
    after_value: Mapped[dict] = mapped_column(JSON, default=dict)
    actor: Mapped[str] = mapped_column(String(80), default="demo-admin")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class InventoryAudit(Base):
    __tablename__ = "inventory_audits"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    product_id: Mapped[str] = mapped_column(String(32))
    before_on_hand: Mapped[int | None] = mapped_column(Integer, nullable=True)
    before_reserved: Mapped[int | None] = mapped_column(Integer, nullable=True)
    after_on_hand: Mapped[int] = mapped_column(Integer)
    after_reserved: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(Text, default="")
    actor: Mapped[str] = mapped_column(String(80), default="demo-admin")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    owner_customer_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="IN_PROGRESS")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConversationState(Base):
    __tablename__ = "conversation_states"
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"), primary_key=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    state_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    role: Mapped[str] = mapped_column(String(20))
    actor_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ConversationGoal(Base):
    __tablename__ = "conversation_goals"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    goal_type: Mapped[str] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(30))
    priority: Mapped[int] = mapped_column(Integer, default=1)
    goal_json: Mapped[dict] = mapped_column(JSON, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EvidenceAttachment(Base):
    __tablename__ = "evidence_attachments"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(ForeignKey("conversations.id"))
    filename: Mapped[str] = mapped_column(String(255), default="image")
    mime_type: Mapped[str] = mapped_column(String(80))
    storage_path: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64))
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class ProductAlias(Base):
    __tablename__ = "product_aliases"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    alias: Mapped[str] = mapped_column(String(120), unique=True)
    product_id: Mapped[str] = mapped_column(String(32))
    alias_type: Mapped[str] = mapped_column(String(40), default="DISPLAY_NAME")
    source: Mapped[str] = mapped_column(String(40), default="MANUAL")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProductMedia(Base):
    __tablename__ = "product_media"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    product_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(40), default="PRODUCT_IMAGE")
    storage_path: Mapped[str] = mapped_column(Text)
    mime_type: Mapped[str] = mapped_column(String(80))
    display_name: Mapped[str] = mapped_column(String(255), default="image")
    alt_text: Mapped[str] = mapped_column(String(255), default="")
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class CustomerMemory(Base):
    __tablename__ = "customer_memories"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(32), index=True)
    memory_type: Mapped[str] = mapped_column(String(40))
    memory_key: Mapped[str] = mapped_column(String(80))
    memory_value: Mapped[dict] = mapped_column(JSON, default=dict)
    source: Mapped[str] = mapped_column(String(40), default="USER_EXPLICIT")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    confirmed: Mapped[bool] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(30), default="ACTIVE")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InventoryReservation(Base):
    __tablename__ = "inventory_reservations"
    reservation_key: Mapped[str] = mapped_column(String(160), primary_key=True)
    reservation_id: Mapped[str] = mapped_column(String(32), unique=True)
    product_id: Mapped[str] = mapped_column(String(32))
    customer_id: Mapped[str] = mapped_column(String(32))
    quantity: Mapped[int] = mapped_column(Integer)
    pickup_time: Mapped[str] = mapped_column(String(80))
    status: Mapped[str] = mapped_column(String(30), default="RESERVED")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
