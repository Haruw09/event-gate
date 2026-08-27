from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    external_id: str
    severity: int = Field(ge=1, le=5)
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime


class EventRead(BaseModel):
    id: int
    source_id: UUID
    external_id: str
    severity: int
    event_type: str
    payload: dict[str, Any]
    occurred_at: datetime
    ingested_at: datetime

    model_config = ConfigDict(from_attributes=True)
