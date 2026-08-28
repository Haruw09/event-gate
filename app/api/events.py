from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.dialects.postgresql import insert

from app.api.deps import get_rate_limited_source, get_session
from app.models.event import Event
from app.models.source import Source
from app.schemas.event import (
    EventBatchCreate,
    EventCreate,
    EventListResponse,
    EventRead,
)
from app.services.correlation import create_alerts_for_event
from app.redis_client import redis_client

from uuid import UUID
from datetime import datetime
from fastapi import Query, APIRouter, Depends, Response, Header


IDEMPOTENCY_TTL_SEC = 24 * 60 * 60

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=201)
async def create_event(
    event: EventCreate,
    response: Response,
    idempotency_key: str = Header(alias="Idempotency-Key"),
    source: Source = Depends(get_rate_limited_source),
    session: AsyncSession = Depends(get_session),
) -> Event:
    source_id = source.id

    redis_key = f"idempotency:{source_id}:{idempotency_key}"

    existing_event_id = await redis_client.get(redis_key)

    if existing_event_id is not None:
        existing_event = await session.get(Event, int(existing_event_id))
        if existing_event is not None:
            response.status_code = 200
            return existing_event

    db_event = Event(
        source_id=source_id,
        external_id=event.external_id,
        severity=event.severity,
        event_type=event.event_type,
        payload=event.payload,
        occurred_at=event.occurred_at,
    )

    try:
        async with session.begin_nested():
            session.add(db_event)
            await session.flush()

    except IntegrityError:
        result = await session.execute(
            select(Event).where(
                Event.source_id == source_id,
                Event.external_id == event.external_id,
            )
        )
        existing_event = result.scalar_one()

        await session.commit()

        await redis_client.set(
            redis_key,
            existing_event.id,
            ex=IDEMPOTENCY_TTL_SEC,
        )

        response.status_code = status.HTTP_200_OK
        return existing_event

    await create_alerts_for_event(session, db_event)

    await session.commit()
    await session.refresh(db_event)

    await redis_client.set(
        redis_key,
        db_event.id,
        ex=IDEMPOTENCY_TTL_SEC,
    )

    return db_event


@router.post("/batch", status_code=status.HTTP_201_CREATED)
async def create_events_batch(
    batch: EventBatchCreate,
    source: Source = Depends(get_rate_limited_source),
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    source_id = source.id

    values = [
        {
            "source_id": source_id,
            "external_id": event.external_id,
            "severity": event.severity,
            "event_type": event.event_type,
            "payload": event.payload,
            "occurred_at": event.occurred_at,
        }
        for event in batch.events
    ]

    stmt = (
        insert(Event)
        .values(values)
        .on_conflict_do_nothing(
            constraint="uq_events_source_external"
        )
    )

    result = await session.execute(stmt)
    await session.commit()

    return {"inserted": result.rowcount}


@router.get("", response_model=EventListResponse)
async def get_events(
    limit: int = 50,
    cursor: int | None = None,
    session: AsyncSession = Depends(get_session),
    source_id: UUID | None = None,
    severity: int | None = None,
    event_type: str | None = None,
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = None,
) -> EventListResponse:
    query = select(Event).order_by(Event.id.desc()).limit(limit)

    if severity is not None:
        query = query.where(Event.severity == severity)

    if event_type is not None:
        query = query.where(Event.event_type == event_type)

    if source_id is not None:
        query = query.where(Event.source_id == source_id)

    if from_ is not None:
        query = query.where(Event.occurred_at >= from_)

    if to is not None:
        query = query.where(Event.occurred_at <= to)

    if cursor is not None:
        query = query.where(Event.id < cursor)

    result = await session.execute(query)
    events = list(result.scalars().all())

    next_cursor = events[-1].id if events else None

    return EventListResponse(
        items=events,
        next_cursor=next_cursor,
    )
