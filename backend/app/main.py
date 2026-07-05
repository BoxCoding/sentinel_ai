"""Sentinel AI — FastAPI application entrypoint (Cloud Run service)."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (agents_ops, auth, chat, dashboard, incidents,
                            location, predictions)
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.rag.knowledge_seed import seed_knowledge_base

setup_logging()
log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    chunks = seed_knowledge_base()
    log.info("startup", demo_mode=settings.DEMO_MODE, kb_chunks=chunks)
    yield


app = FastAPI(
    title="Sentinel AI — Emergency Decision Intelligence Platform",
    description="AI that predicts emergencies before they become disasters.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, incidents.router, predictions.router,
               chat.router, agents_ops.router, dashboard.router, location.router):
    app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.get("/healthz", tags=["ops"])
async def healthz():
    return {"status": "ok", "service": settings.APP_NAME, "demo_mode": settings.DEMO_MODE}
