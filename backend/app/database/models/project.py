import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database.postgres import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    health = Column(String(20), nullable=False, default="healthy")  # healthy, at_risk, blocked, completed
    reason = Column(Text, nullable=True, default="Project milestone tracking active.")
    completed_tasks = Column(Integer, nullable=False, default=0)
    total_tasks = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "health": self.health,
            "reason": self.reason,
            "completedTasks": self.completed_tasks,
            "completed_tasks": self.completed_tasks,
            "totalTasks": self.total_tasks,
            "total_tasks": self.total_tasks,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
