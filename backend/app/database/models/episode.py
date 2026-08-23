from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Enum, JSON
from sqlalchemy.sql import func
from app.database.postgres import Base

class EpisodeOutcome(str, PyEnum):
    SUCCESS = 'success'
    PARTIAL = 'partial'
    FAILURE = 'failure'
    ABANDONED = 'abandoned'

class Episode(Base):
    __tablename__ = 'episodes'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    context = Column(String(100), nullable=False)
    project = Column(String(200), nullable=True)
    task = Column(String(300), nullable=True)
    goal = Column(Text, nullable=True)
    problem = Column(Text, nullable=True)
    decision = Column(Text, nullable=True)
    outcome = Column(Enum(EpisodeOutcome), nullable=True)
    confidence = Column(Float, nullable=False, default=0.5)
    tags = Column(JSON, nullable=True)
    related_episode_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {'id': self.id, 'context': self.context, 'project': self.project, 'task': self.task, 'goal': self.goal, 'problem': self.problem, 'decision': self.decision, 'outcome': self.outcome.value if self.outcome else None, 'confidence': self.confidence, 'tags': self.tags, 'related_episode_id': self.related_episode_id, 'created_at': self.created_at.isoformat() if self.created_at else None}

    def __repr__(self) -> str:
        return f'<Episode id={self.id} context={self.context} outcome={self.outcome}>'
