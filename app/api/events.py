from fastapi import APIRouter, Depends

from app.api.deps import get_current_source
from app.models.source import Source

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.post("")
async def create_event(
    source: Source = Depends(get_current_source),
) -> dict[str, str]:
    return {"source": source.name}
