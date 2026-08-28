from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class SourceStatsRead(BaseModel):
    source_id: UUID
    source_name: str
    event_count: int
    alert_count: int
    avg_severity: float | None
    last_event_at: datetime | None
    event_share_percent: float
