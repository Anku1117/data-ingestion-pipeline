from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from services.detector.engine import DetectionEngine

logger_text = __import__("logging").getLogger(__name__)
router = APIRouter(prefix="/threats", tags=["threats"])

_engine: DetectionEngine | None = None


def _get_engine() -> DetectionEngine:
    global _engine
    if _engine is None:
        _engine = DetectionEngine()
    return _engine


@router.get("")
async def list_threats(
    threat_type: str | None = Query(None, description="Filter by threat type"),
    severity: str | None = Query(None, description="Filter by severity"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    engine = _get_engine()
    return engine.get_alerts(threat_type=threat_type, severity=severity, limit=limit, offset=offset)


@router.get("/rules")
async def list_rules() -> list[dict]:
    engine = _get_engine()
    return engine.get_rules()


@router.get("/stats")
async def threat_stats() -> dict:
    engine = _get_engine()
    return engine.get_stats()


@router.get("/{alert_id}")
async def get_threat(alert_id: str) -> dict:
    engine = _get_engine()
    alert = engine.get_alert_by_id(alert_id)
    if alert is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "detail": f"Alert {alert_id} not found"},
        )
    return alert.model_dump(mode="json")
