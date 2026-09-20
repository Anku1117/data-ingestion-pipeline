from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Request, status

from libraries.configuration.settings import get_settings
from libraries.logging.logging import get_logger
from libraries.schemas.common import EventEnvelope
from services.ingestion.producer import get_producer
from services.ingestion.schemas import (
    ErrorResponse,
    EventCreateRequest,
    EventCreateResponse,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/events", tags=["events"])


@router.post(
    "",
    response_model=EventCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)
async def create_event(request: Request, body: EventCreateRequest) -> EventCreateResponse:
    request_id = str(uuid.uuid4())
    settings = get_settings()

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

        producer = get_producer()
        await producer.produce(settings.kafka_events_topic, event)

        logger.info(
            "Event accepted event_id=%s event_type=%s request_id=%s",
            event.event_id,
            event.event_type,
            request_id,
        )

        return EventCreateResponse(
            event_id=event.event_id,
            status="accepted",
            timestamp=event.timestamp,
        )
    except Exception as e:
        logger.error("Failed to create event request_id=%s error=%s", request_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                error="event_creation_failed",
                detail=str(e),
                request_id=request_id,
            ).model_dump(),
        ) from e
