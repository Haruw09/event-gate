import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "source_id",
            "external_id",
            name="uq_events_source_external",
        ),
        CheckConstraint(
            "severity BETWEEN 1 AND 5",
            name="ck_events_severity_range",
        ),
        Index(
            "ix_events_source_occurred_at",
            "source_id",
            occurred_at.desc(),
        ),
        Index(
            "ix_events_type_severity",
            "event_type",
            "severity",
        ),
    )
