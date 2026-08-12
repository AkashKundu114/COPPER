"""
Structured user-memory model: Fact / Observation / Hypothesis.
Replaces the flat `Memory` model (see database/models/memory.py, deprecated).
Master System Prompt §7-8.
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, JSON
from sqlalchemy.sql import func
from app.database.postgres import Base


class MemoryType(str, PyEnum):
    FACT = "fact"                # explicitly stated or reliably verified
    OBSERVATION = "observation"  # derived from repeated behavior
    HYPOTHESIS = "hypothesis"    # tentative interpretation, low confidence


class MemoryStatus(str, PyEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"        # user marked incorrect / asked to forget


class UserMemoryV2(Base):
    __tablename__ = "user_memories_v2"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)

    content = Column(Text, nullable=False)
    type = Column(Enum(MemoryType), nullable=False, default=MemoryType.OBSERVATION)
    category = Column(String(50), nullable=True)  # goal | preference | habit | project | constraint...

    source = Column(String(100), nullable=True)   # chat | file | voice | manual | inferred
    confidence = Column(Float, nullable=False, default=0.5)  # 0.0-1.0
    evidence_count = Column(Integer, nullable=False, default=1)

    status = Column(Enum(MemoryStatus), nullable=False, default=MemoryStatus.ACTIVE)
    supersedes_id = Column(Integer, nullable=True)  # points at the memory it replaced, if any

    extra_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_confirmed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "content": self.content,
            "type": self.type.value if self.type else None,
            "category": self.category,
            "source": self.source,
            "confidence": self.confidence,
            "evidence_count": self.evidence_count,
            "status": self.status.value if self.status else None,
            "supersedes_id": self.supersedes_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_confirmed_at": self.last_confirmed_at.isoformat() if self.last_confirmed_at else None,
        }

    def __repr__(self) -> str:
        return f"<UserMemoryV2 id={self.id} type={self.type} conf={self.confidence:.2f}>"


# Conflict-resolution priority, per Master System Prompt §29:
#   recent explicit statement > older explicit statement > repeated observation
#   > single observation > hypothesis
MEMORY_PRIORITY = {
    MemoryType.FACT: 3,
    MemoryType.OBSERVATION: 2,
    MemoryType.HYPOTHESIS: 1,
}
