from datetime import timedelta

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.rule import Rule
from app.models.alert import Alert


async def get_matching_rules(
    session: AsyncSession,
    event: Event,
) -> list[Rule]:
    stmt = select(Rule).where(
        Rule.is_active.is_(True),
        or_(Rule.source_id == event.source_id, Rule.source_id.is_(None)),
        or_(Rule.event_type == event.event_type, Rule.event_type.is_(None)),
        Rule.min_severity <= event.severity,
    )

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def count_matching_events(
    session: AsyncSession,
    event: Event,
    rule: Rule,
) -> int:
    window_start = event.occurred_at - timedelta(seconds=rule.window_sec)

    stmt = select(func.count(Event.id)).where(
        Event.source_id == event.source_id,
        Event.event_type == event.event_type,
        Event.severity >= rule.min_severity,
        Event.occurred_at >= window_start,
        Event.occurred_at <= event.occurred_at,
    )

    result = await session.execute(stmt)
    return result.scalar_one()


async def correlate_event(
    session: AsyncSession,
    event: Event,
) -> list[tuple[Rule, int]]:
    matched_rules = await get_matching_rules(session, event)

    triggered: list[tuple[Rule, int]] = []

    for rule in matched_rules:
        count = await count_matching_events(session, event, rule)

        if count >= rule.threshold:
            triggered.append((rule, count))

    return triggered


async def create_alerts_for_event(
    session: AsyncSession,
    event: Event,
) -> list[Alert]:
    triggered = await correlate_event(session, event)

    alerts: list[Alert] = []

    for rule, count in triggered:
        window_start = event.occurred_at - timedelta(seconds=rule.window_sec)

        alert = Alert(
            rule_id=rule.id,
            source_id=event.source_id,
            matched_count=count,
            window_start=window_start,
            window_end=event.occurred_at,
        )

        session.add(alert)
        alerts.append(alert)

    return alerts
