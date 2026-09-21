from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from libraries.configuration.settings import get_settings
from libraries.database.session import dispose_engine, get_engine
from libraries.event_backend import start_event_backend, stop_event_backend
from libraries.logging.logging import get_logger, setup_logging
from services.ingestion.routes import (
    agents,
    events,
    events_query,
    health,
    metrics,
    pipeline,
    prometheus,
    threats,
)

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = get_logger(__name__)

_SHUTDOWN_TIMEOUT = 30


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    settings = get_settings()
    app.state.settings = settings

    engine = get_engine()
    app.state.engine = engine

    await start_event_backend()
    logger.info("DIP started (env=%s)", settings.env)

    yield

    logger.info("DIP shutting down (drain timeout=%ds)", _SHUTDOWN_TIMEOUT)
    try:
        await asyncio.wait_for(stop_event_backend(), timeout=_SHUTDOWN_TIMEOUT)
    except asyncio.TimeoutError:
        logger.warning("Event backend shutdown timed out after %ds", _SHUTDOWN_TIMEOUT)

    await dispose_engine()
    logger.info("DIP shutdown complete")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="DIP — Data Ingestion Platform",
        description="Production-grade event-driven data ingestion platform",
        version="0.2.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(events.router)
    app.include_router(events_query.router)
    app.include_router(agents.router)
    app.include_router(threats.router)
    app.include_router(pipeline.router)
    app.include_router(metrics.router)
    app.include_router(prometheus.router)

    return app


app = create_app()
