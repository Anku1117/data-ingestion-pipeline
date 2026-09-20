from __future__ import annotations

from fastapi import APIRouter, Response

from libraries.observability.prometheus import generate_prometheus_metrics

logger_text = __import__("logging").getLogger(__name__)
router = APIRouter(tags=["prometheus"])


@router.get("/prometheus")
async def prometheus_metrics() -> Response:
    content = generate_prometheus_metrics()
    return Response(content=content, media_type="text/plain; version=0.0.4; charset=utf-8")
