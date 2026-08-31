from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database.postgres import Base


class SelfMemoryCategory(str, PyEnum):
    DECISION = "decision"
    CORRECTION = "correction"
    POSITION = "position"
    TRACK_RECORD = "track_record"
    OPEN_QUESTION = "open_question"


class SelfMemoryOutcome(str, PyEnum):
    CONFIRMED_HELPFUL = "confirmed_helpful"
    CONFIRMED_WRONG = "confirmed_wrong"
    UNKNOWN = "unknown"


class SelfMemory(Base):
    __tablename__ = "self_memory"
    id = Column(String(64), primary_key=True)
    category = Column(Enum(SelfMemoryCategory), nullable=False)
    content = Column(Text, nullable=False)
    outcome = Column(Enum(SelfMemoryOutcome), nullable=True)
    confidence = Column(Float, nullable=False, default=0.5)
    evidence_count = Column(Integer, nullable=False, default=1)
    related_episode_id = Column(Integer, nullable=True)
    superseded_by = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_reinforced_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category.value if self.category else None,
            "content": self.content,
            "outcome": self.outcome.value if self.outcome else None,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "related_episode_id": self.related_episode_id,
            "superseded_by": self.superseded_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_reinforced_at": self.last_reinforced_at.isoformat() if self.last_reinforced_at else None,
        }

    def __repr__(self) -> str:
        return f"<SelfMemory id={self.id} category={self.category} conf={self.confidence:.2f}>"
