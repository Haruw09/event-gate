from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleRead, RuleUpdate

router = APIRouter(prefix="/api/v1/rules", tags=["rules"])


@router.post("", response_model=RuleRead, status_code=201)
async def create_rule(
    rule: RuleCreate,
    session: AsyncSession = Depends(get_session),
) -> Rule:
    db_rule = Rule(
        name=rule.name,
        source_id=rule.source_id,
        event_type=rule.event_type,
        min_severity=rule.min_severity,
        threshold=rule.threshold,
        window_sec=rule.window_sec,
    )

    session.add(db_rule)
    await session.commit()
    await session.refresh(db_rule)

    return db_rule


@router.get("", response_model=list[RuleRead])
async def get_rules(
    session: AsyncSession = Depends(get_session),
) -> list[Rule]:
    result = await session.execute(select(Rule))
    return list(result.scalars().all())


@router.patch("/{rule_id}", response_model=RuleRead)
async def update_rule(
    rule_id: UUID,
    rule_update: RuleUpdate,
    session: AsyncSession = Depends(get_session),
) -> Rule:
    db_rule = await session.get(Rule, rule_id)

    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")

    update_data = rule_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(db_rule, field, value)

    await session.commit()
    await session.refresh(db_rule)

    return db_rule