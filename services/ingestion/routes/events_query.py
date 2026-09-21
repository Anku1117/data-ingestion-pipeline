from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from libraries.database.repositories import SQLAlchemyEventRepository
from libraries.database.session import get_session
from libraries.logging.logging import get_logger
from libraries.search import get_search

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events(
    event_type: str | None = Query(None, description="Filter by event type"),
    source: str | None = Query(None, description="Filter by source"),
    severity: str | None = Query(None, description="Filter by severity"),
    agent_id: str | None = Query(None, description="Filter by agent ID"),
    limit: int = Query(50, ge=1, le=200, description="Page size"),
    offset: int = Query(0, ge=0, description="Offset"),
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict:
    search = get_search()
    result = await search.search_events(
        event_type=event_type,
        source=source,
        severity=severity,
        agent_id=agent_id,
        limit=limit,
        offset=offset,
    )
    return result


@router.get("/{event_id}")
async def get_event(
    event_id: str,
    session: AsyncSession = Depends(get_session),  # noqa: B008
) -> dict:
    search = get_search()
    event = await search.get_event(event_id)
    if event is not None:
        return event

    repo = SQLAlchemyEventRepository(session)
    record = await repo.get_event_by_id(event_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": "not_found", "detail": f"Event {event_id} not found"},
        )
    return {
        "event_id": record.event_id,
        "event_version": record.event_version,
        "event_type": record.event_type,
        "source": record.source,
        "producer": record.producer,
        "severity": record.severity,
        "timestamp": record.timestamp.isoformat() if record.timestamp else None,
        "payload": record.payload,
        "metadata": record.metadata_,
        "trace_id": record.trace_id,
        "agent_id": record.agent_id,
        "run_id": record.run_id,
        "tenant_id": record.tenant_id,
        "session_id": record.session_id,
        "schema_version": record.schema_version,
    }
