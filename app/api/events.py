from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.api.deps import get_current_source, get_session
from app.models.event import Event
from app.models.source import Source
from app.schemas.event import EventCreate, EventRead

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("", response_model=EventRead, status_code=201)
async def create_event(
    event: EventCreate,
    response: Response,
    source: Source = Depends(get_current_source),
    session: AsyncSession = Depends(get_session),
) -> Event:
    source_id = source.id

    db_event = Event(
        source_id=source.id,
        external_id=event.external_id,
        severity=event.severity,
        event_type=event.event_type,
        payload=event.payload,
        occurred_at=event.occurred_at,
    )

    session.add(db_event)

    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()

        result = await session.execute(
            select(Event).where(
                Event.source_id == source_id,
                Event.external_id == event.external_id,
            )
        )
        existing_event = result.scalar_one()

        response.status_code = status.HTTP_200_OK
        return existing_event

    await session.refresh(db_event)
    return db_event
