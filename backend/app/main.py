import structlog
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app import logging as app_logging
from app.api.events import router as events_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once on startup (before yield) and once on shutdown (after yield)."""
    app_logging.configure_logging(settings.log_level)
    logger.info("meridian_starting", env=settings.app_env, llm_provider=settings.llm_provider)
    yield
    logger.info("meridian_stopped")


app = FastAPI(
    title="Meridian",
    description="Multi-agent due diligence for Indian public companies",
    version="0.1.0",
    lifespan=lifespan,
)

# Allow the Next.js frontend (port 3000) to call this API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    """Liveness check. Returns 200 if the server is up."""
    return {"status": "ok", "env": settings.app_env}
