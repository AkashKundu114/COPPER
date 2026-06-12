from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from app.database.postgres import Base


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_rule = Column(String(100), nullable=True)
    is_completed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "is_recurring": self.is_recurring,
            "recurrence_rule": self.recurrence_rule,
            "is_completed": self.is_completed,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<Reminder id={self.id} title={self.title!r} due_at={self.due_at}>"
