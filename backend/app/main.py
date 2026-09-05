import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from .api.sessions import router
from .api.confirmations import router as confirmation_router
from .api.handoff import router as handoff_router
from .api.returns import router as return_router
from .api.trace import router as trace_router
from .api.admin import router as admin_router
from .api.media import router as media_router
from .api.memory import router as memory_router
from .api.order_emails import router as order_email_router
from .api.order_drafts import router as order_draft_router
from .api.order_replies import router as order_reply_router
from .api.pqg import router as pqg_router
from .domain.business_config import load_persisted
from .db.seed import load_products_from_seed, seed_inventory, seed_media_and_aliases, sync_product_rows

app = FastAPI(title="Shanye Shop Demo Customer Service Agent", version="0.1.0")
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.include_router(confirmation_router)
app.include_router(handoff_router)
app.include_router(return_router)
app.include_router(trace_router)
app.include_router(admin_router)
app.include_router(media_router)
app.include_router(memory_router)
app.include_router(order_email_router)
app.include_router(order_draft_router)
app.include_router(order_reply_router)
app.include_router(pqg_router)
load_products_from_seed()
load_persisted()
seed_inventory()
sync_product_rows()
seed_media_and_aliases()

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return {"service": "shanye-shop-agent", "status": "ok", "docs": "/docs"}
