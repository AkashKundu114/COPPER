from enum import Enum as PyEnum

from sqlalchemy import JSON, Column, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database.postgres import Base


class MemoryType(str, PyEnum):
    FACT = "fact"
    OBSERVATION = "observation"
    HYPOTHESIS = "hypothesis"


class MemoryStatus(str, PyEnum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    REJECTED = "rejected"
    QUARANTINED = "quarantined"
    EXPIRED = "expired"
    ARCHIVED = "archived"


class UserMemoryV2(Base):
    __tablename__ = "user_memories_v2"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    content = Column(Text, nullable=False)
    type = Column(Enum(MemoryType), nullable=False, default=MemoryType.OBSERVATION)
    category = Column(String(50), nullable=True)
    source = Column(String(100), nullable=True)
    confidence = Column(Float, nullable=False, default=0.5)
    evidence_count = Column(Integer, nullable=False, default=1)
    status = Column(Enum(MemoryStatus), nullable=False, default=MemoryStatus.ACTIVE)
    supersedes_id = Column(Integer, nullable=True)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_confirmed_at = Column(DateTime(timezone=True), nullable=True)

    @property
    def importance(self) -> float:
        if self.extra_metadata and "importance" in self.extra_metadata:
            return float(self.extra_metadata["importance"])
        if self.type == MemoryType.FACT:
            return 0.90
        elif self.type == MemoryType.OBSERVATION:
            return 0.50
        return 0.25

    @importance.setter
    def importance(self, val: float):
        d = dict(self.extra_metadata or {})
        d["importance"] = max(0.05, min(1.0, float(val)))
        self.extra_metadata = d

    @property
    def retrieval_count(self) -> int:
        if self.extra_metadata and "retrieval_count" in self.extra_metadata:
            return int(self.extra_metadata["retrieval_count"])
        return 0

    @retrieval_count.setter
    def retrieval_count(self, val: int):
        d = dict(self.extra_metadata or {})
        d["retrieval_count"] = max(0, int(val))
        self.extra_metadata = d

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "content": self.content,
            "type": self.type.value if hasattr(self.type, "value") else str(self.type),
            "category": self.category,
            "source": self.source,
            "confidence": round(self.confidence, 3),
            "importance": round(self.importance, 2),
            "evidence_count": self.evidence_count,
            "retrieval_count": self.retrieval_count,
            "status": self.status.value if hasattr(self.status, "value") else str(self.status),
            "supersedes_id": self.supersedes_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_confirmed_at": self.last_confirmed_at.isoformat() if self.last_confirmed_at else None,
        }


MEMORY_PRIORITY = {
    MemoryType.FACT: 3,
    MemoryType.OBSERVATION: 2,
    MemoryType.HYPOTHESIS: 1,
}
