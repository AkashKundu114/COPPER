import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime
from app.database.postgres import Base

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(64), nullable=False, index=True)
    sender = Column(String(16), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))