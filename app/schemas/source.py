from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SourceCreate(BaseModel):
    name: str
    api_key: str


class SourceRead(BaseModel):
    id: UUID
    name: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SourceUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None
