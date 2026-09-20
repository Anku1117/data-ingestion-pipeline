from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from libraries.configuration.settings import get_settings
from libraries.database.session import dispose_engine, get_engine
from libraries.event_backend import start_event_backend, stop_event_backend
from libraries.logging.logging import setup_logging
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


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    settings = get_settings()
    app.state.settings = settings

    engine = get_engine()
    app.state.engine = engine

    await start_event_backend()

    yield

    await stop_event_backend()
    await dispose_engine()


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
        allow_origins=["*"] if settings.debug else [],
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
