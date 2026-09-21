from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request, status

from libraries.database.repositories import DuplicateEventError, SQLAlchemyEventRepository
from libraries.database.session import get_session
from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope
from libraries.search import get_search
from libraries.security.auth import verify_api_key
from libraries.security.rate_limit import rate_limit
from services.ingestion.schemas import (
    ErrorResponse,
    EventCreateRequest,
    EventCreateResponse,
)
from services.ingestion.service import EventService

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


def _get_service(session: AsyncSession) -> EventService:
    repo = SQLAlchemyEventRepository(session)
    return EventService(repo)


@router.post(
    "",
    response_model=EventCreateResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_event(
    request: Request,
    body: EventCreateRequest,
    session: AsyncSession = Depends(get_session),  # noqa: B008
    _api_key: str | None = Depends(verify_api_key),  # noqa: B008
    _rate: None = Depends(rate_limit),  # noqa: B008
) -> EventCreateResponse:
    request_id = str(uuid.uuid4())

    try:
        kwargs: dict[str, object] = {
            "event_type": body.event_type,
            "source": body.source,
            "producer": body.producer,
            "payload": body.payload,
            "severity": body.severity,
            "metadata": body.metadata,
            "tenant_id": body.tenant_id,
            "trace_id": body.trace_id or str(uuid.uuid4()),
        }
        if body.timestamp is not None:
            kwargs["timestamp"] = body.timestamp
        event = EventEnvelope(**kwargs)

        service = _get_service(session)
        await service.create_event(event)
        await session.commit()

        try:
            search = get_search()
            await search.index_event(event)
        except Exception:
            logger.warning("Failed to index event in search backend event_id=%s", event.event_id)

        logger.info(
            "Event persisted event_id=%s event_type=%s request_id=%s",
            event.event_id,
            event.event_type,
            request_id,
        )

        return EventCreateResponse(
            event_id=event.event_id,
            status="created",
            timestamp=event.timestamp,
        )
    except DuplicateEventError as e:
        await session.rollback()
        logger.warning("Duplicate event event_id=%s request_id=%s", e.event_id, request_id)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error="duplicate_event",
                detail=f"Event with id '{e.event_id}' already exists",
                request_id=request_id,
            ).model_dump(),
        ) from None
    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        logger.error("Failed to create event request_id=%s error=%s", request_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="event_creation_failed",
                detail="Internal server error",
                request_id=request_id,
            ).model_dump(),
        ) from e
