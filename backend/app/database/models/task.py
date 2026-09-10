import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String

from app.database.postgres import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    project = Column(String(100), nullable=False, default="General")
    priority = Column(String(20), nullable=False, default="medium")  # high, medium, low
    duration = Column(String(50), nullable=False, default="30m")
    status = Column(String(20), nullable=False, default="inbox")  # inbox, planned, active, completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_dict(self) -> dict:
        created_timestamp = int(self.created_at.timestamp() * 1000) if self.created_at else 0
        return {
            "id": self.id,
            "title": self.title,
            "project": self.project,
            "priority": self.priority,
            "duration": self.duration,
            "status": self.status,
            "createdAt": created_timestamp,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
