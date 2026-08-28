from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.alert import Alert
from app.schemas.alert import AlertRead, AlertStatus, AlertUpdate

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
async def get_alerts(
    status: AlertStatus | None = None,
    session: AsyncSession = Depends(get_session),
) -> list[Alert]:
    query = select(Alert).order_by(Alert.created_at.desc())

    if status is not None:
        query = query.where(Alert.status == status)

    result = await session.execute(query)
    return list(result.scalars().all())


@router.patch("/{alert_id}", response_model=AlertRead)
async def update_alert(
    alert_id: UUID,
    alert_update: AlertUpdate,
    session: AsyncSession = Depends(get_session),
) -> Alert:
    db_alert = await session.get(Alert, alert_id)

    if db_alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    db_alert.status = alert_update.status

    await session.commit()
    await session.refresh(db_alert)

    return db_alert
