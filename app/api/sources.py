from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.models.source import Source
from app.schemas.source import SourceCreate, SourceRead

router = APIRouter(prefix="/api/v1/sources", tags=["sources"])


@router.post("", response_model=SourceRead, status_code=201)
async def create_source(
    source: SourceCreate,
    session: AsyncSession = Depends(get_session),
) -> Source:
    db_source = Source(
        name=source.name,
        api_key=source.api_key,
    )

    session.add(db_source)
    await session.commit()
    await session.refresh(db_source)

    return db_source
