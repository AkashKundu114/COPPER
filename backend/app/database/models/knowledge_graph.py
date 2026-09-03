from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from app.database.postgres import Base


class KnowledgeEntity(Base):
    __tablename__ = "knowledge_entities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    canonical_name = Column(String(255), nullable=False, unique=True, index=True)
    entity_type = Column(String(64), nullable=False, default="CONCEPT", index=True)
    confidence = Column(Float, nullable=False, default=0.8)
    context = Column(Text, nullable=True)
    evidence_count = Column(Integer, nullable=False, default=1)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "canonical_name": self.canonical_name,
            "type": self.entity_type,
            "confidence": round(self.confidence, 3),
            "context": self.context,
            "evidence_count": self.evidence_count,
            "metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<KnowledgeEntity id={self.id} name='{self.name}' type='{self.entity_type}' conf={self.confidence:.2f}>"


class KnowledgeRelationship(Base):
    __tablename__ = "knowledge_relationships"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=True, index=True)
    target_id = Column(Integer, ForeignKey("knowledge_entities.id", ondelete="CASCADE"), nullable=True, index=True)
    source_name = Column(String(255), nullable=False, index=True)
    target_name = Column(String(255), nullable=False, index=True)
    relation_type = Column(String(64), nullable=False, default="RELATED_TO", index=True)
    confidence = Column(Float, nullable=False, default=0.8)
    context = Column(Text, nullable=True)
    evidence_count = Column(Integer, nullable=False, default=1)
    extra_metadata = Column("metadata", JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "source": self.source_name,
            "target": self.target_name,
            "type": self.relation_type,
            "confidence": round(self.confidence, 3),
            "context": self.context,
            "evidence_count": self.evidence_count,
            "metadata": self.extra_metadata or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return (
            f"<KnowledgeRelationship id={self.id} "
            f"'{self.source_name}' -[{self.relation_type}]-> '{self.target_name}' conf={self.confidence:.2f}>"
        )
