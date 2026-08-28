from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RuleCreate(BaseModel):
    name: str
    source_id: UUID | None = None
    event_type: str | None = None
    min_severity: int = Field(default=1, ge=1, le=5)
    threshold: int = Field(gt=0)
    window_sec: int = Field(gt=0)


class RuleUpdate(BaseModel):
    name: str | None = None
    source_id: UUID | None = None
    event_type: str | None = None
    min_severity: int | None = Field(default=None, ge=1, le=5)
    threshold: int | None = Field(default=None, gt=0)
    window_sec: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class RuleRead(BaseModel):
    id: UUID
    name: str
    source_id: UUID | None
    event_type: str | None
    min_severity: int
    threshold: int
    window_sec: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
