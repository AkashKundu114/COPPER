from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, JSON
from sqlalchemy.sql import func
from app.database.postgres import Base

class MemoryType(str, PyEnum):
    FACT = 'fact'
    OBSERVATION = 'observation'
    HYPOTHESIS = 'hypothesis'

class MemoryStatus(str, PyEnum):
    ACTIVE = 'active'
    SUPERSEDED = 'superseded'
    REJECTED = 'rejected'

class UserMemoryV2(Base):
    __tablename__ = 'user_memories_v2'
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
    extra_metadata = Column('metadata', JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_confirmed_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {'id': self.id, 'content': self.content, 'type': self.type.value if self.type else None, 'category': self.category, 'source': self.source, 'confidence': self.confidence, 'evidence_count': self.evidence_count, 'status': self.status.value if self.status else None, 'supersedes_id': self.supersedes_id, 'created_at': self.created_at.isoformat() if self.created_at else None, 'updated_at': self.updated_at.isoformat() if self.updated_at else None, 'last_confirmed_at': self.last_confirmed_at.isoformat() if self.last_confirmed_at else None}

    def __repr__(self) -> str:
        return f'<UserMemoryV2 id={self.id} type={self.type} conf={self.confidence:.2f}>'
MEMORY_PRIORITY = {MemoryType.FACT: 3, MemoryType.OBSERVATION: 2, MemoryType.HYPOTHESIS: 1}