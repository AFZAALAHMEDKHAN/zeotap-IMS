import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.postgres import Base


VALID_CATEGORIES = [
    "DATABASE_FAILURE",
    "CACHE_FAILURE",
    "NETWORK_ISSUE",
    "APPLICATION_BUG",
    "INFRASTRUCTURE",
    "THIRD_PARTY",
    "HUMAN_ERROR",
    "UNKNOWN",
]


class RCA(Base):
    __tablename__ = "rcas"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    workitem_id: Mapped[str] = mapped_column(
        String, ForeignKey("work_items.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    incident_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    incident_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    root_cause_category: Mapped[str] = mapped_column(String, nullable=False)
    fix_applied: Mapped[str] = mapped_column(Text, nullable=False)
    prevention_steps: Mapped[str] = mapped_column(Text, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Back-reference to WorkItem
    work_item: Mapped["WorkItem"] = relationship(  # noqa: F821
        "WorkItem", back_populates="rca"
    )
