from __future__ import annotations

from fastapi import APIRouter

from libraries.configuration.settings import get_settings
from services.ingestion.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version="0.1.0",
        environment=settings.env,
    )


@router.get("/ready")
async def readiness_check() -> dict[str, str]:
    return {"status": "ready"}
