import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    Text,
    func,
    true,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id"),
        nullable=True,
    )
    event_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_severity: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        server_default="1",
    )
    threshold: Mapped[int] = mapped_column(Integer, nullable=False)
    window_sec: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=true(),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        CheckConstraint(
            "min_severity BETWEEN 1 AND 5",
            name="ck_rules_min_severity_range",
        ),
        CheckConstraint(
            "threshold > 0",
            name="ck_rules_threshold_positive",
        ),
        CheckConstraint(
            "window_sec > 0",
            name="ck_rules_window_sec_positive",
        ),
    )