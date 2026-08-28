from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


AlertStatus = Literal["open", "acknowledged", "resolved"]


class AlertUpdate(BaseModel):
    status: AlertStatus


class AlertRead(BaseModel):
    id: UUID
    rule_id: UUID
    source_id: UUID
    matched_count: int
    window_start: datetime
    window_end: datetime
    status: AlertStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
