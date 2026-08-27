from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import SessionLocal
from app.models.source import Source
from app.services.ratelimit import WINDOW_SEC, check_rate_limit
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def get_api_key(
    x_api_key: str = Header(alias="X-API-Key"),
) -> str:
    return x_api_key


async def get_current_source(
    api_key: str = Depends(get_api_key),
    session: AsyncSession = Depends(get_session),
) -> Source:
    result = await session.execute(
        select(Source).where(Source.api_key == api_key)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Source is inactive",
        )

    return source


async def get_rate_limited_source(
    source: Source = Depends(get_current_source),
) -> Source:
    allowed = await check_rate_limit(source.id)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(WINDOW_SEC)},
        )

    return source