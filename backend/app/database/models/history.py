import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, String, Text

from app.database.postgres import Base


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), nullable=False, index=True)
    sender = Column(String(16), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "sender": self.sender,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
