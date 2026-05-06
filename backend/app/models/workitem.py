import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Float, DateTime, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.postgres import Base
import enum


class WorkItemStatus(str, enum.Enum):
    OPEN = "OPEN"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Priority(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class WorkItem(Base):
    __tablename__ = "work_items"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    component_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[WorkItemStatus] = mapped_column(
        SAEnum(WorkItemStatus), default=WorkItemStatus.OPEN, nullable=False
    )
    priority: Mapped[Priority] = mapped_column(
        SAEnum(Priority), nullable=False
    )
    alert_type: Mapped[str] = mapped_column(String, nullable=False)
    signal_count: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    mttr_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationship to RCA (one-to-one)
    rca: Mapped["RCA"] = relationship(  # noqa: F821
        "RCA", back_populates="work_item", uselist=False, lazy="noload"
    )
