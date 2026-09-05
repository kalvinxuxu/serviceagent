import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./runtime/db/shanye_demo.db")
# Railway exposes PostgreSQL URLs without a SQLAlchemy driver suffix. Use the
# psycopg v3 driver installed by this project instead of SQLAlchemy's legacy
# psycopg2 default.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgres://"):]
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = "postgresql+psycopg://" + DATABASE_URL[len("postgresql://"):]
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {"connect_timeout": 10}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    from . import models  # noqa: F401
    from .base import Base
    if DATABASE_URL.startswith("sqlite"):
        # SQLite does not create missing parent directories.  Tests and CLI
        # commands may run from either the repository root or backend/, so
        # ensure the configured database directory exists before create_all.
        database_path = DATABASE_URL.removeprefix("sqlite:///")
        parent = os.path.dirname(os.path.abspath(database_path))
        if parent:
            os.makedirs(parent, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    # Keep the demo SQLite database usable when models gain additive fields.
    if DATABASE_URL.startswith("sqlite"):
        product_columns = {column["name"] for column in inspect(engine).get_columns("products")}
        for name, definition in {"profile": "JSON", "price_channel": "VARCHAR(30)", "member_price": "FLOAT", "promotion_price": "FLOAT", "status": "VARCHAR(20)"}.items():
            if name not in product_columns:
                with engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE products ADD COLUMN {name} {definition}"))
        columns = {column["name"] for column in inspect(engine).get_columns("agent_steps")}
        if "created_at" not in columns:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE agent_steps ADD COLUMN created_at DATETIME"))
        step_additions = {
            "component": "VARCHAR(60)", "turn_id": "VARCHAR(40)",
            "input_snapshot": "JSON", "output_snapshot": "JSON",
            "before_state": "JSON", "after_state": "JSON",
            "latency_ms": "FLOAT", "step_status": "VARCHAR(30)",
            "error_code": "VARCHAR(120)",
        }
        for name, definition in step_additions.items():
            if name not in columns:
                with engine.begin() as connection:
                    connection.execute(text(f"ALTER TABLE agent_steps ADD COLUMN {name} {definition}"))
        handoff_columns = {column["name"] for column in inspect(engine).get_columns("human_handoffs")}
        additions = {
            "original_request": "TEXT",
            "known_facts": "JSON",
            "completed_steps": "JSON",
            "pending_items": "JSON",
        }
        missing = [(name, definition) for name, definition in additions.items() if name not in handoff_columns]
        if missing:
            with engine.begin() as connection:
                for name, definition in missing:
                    connection.execute(text(f"ALTER TABLE human_handoffs ADD COLUMN {name} {definition}"))
        conversations = {column["name"] for column in inspect(engine).get_columns("conversations")}
        if "owner_customer_id" not in conversations:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE conversations ADD COLUMN owner_customer_id VARCHAR(32)"))
        messages = {column["name"] for column in inspect(engine).get_columns("conversation_messages")}
        if "actor_id" not in messages:
            with engine.begin() as connection:
                connection.execute(text("ALTER TABLE conversation_messages ADD COLUMN actor_id VARCHAR(32)"))
