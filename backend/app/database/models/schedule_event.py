import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, String

from app.database.postgres import Base


class ScheduleEvent(Base):
    __tablename__ = "schedule_events"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    time = Column(String(50), nullable=False)  # e.g. "10:00 AM"
    title = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, default="Focus")  # Focus, Meeting, Break, Review
    completed = Column(Boolean, nullable=False, default=False)
    date = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "time": self.time,
            "title": self.title,
            "category": self.category,
            "completed": self.completed,
            "date": self.date,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
