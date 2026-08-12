"""
Agent Registry — discovery, versioning, hot-swap, rollback.
Master System Prompt §13-14, Master UI Prompt §13-14.
"""
from enum import Enum as PyEnum
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, JSON, Enum
from sqlalchemy.sql import func
from app.database.postgres import Base


class AgentStatus(str, PyEnum):
    ACTIVE = "active"
    CANDIDATE = "candidate"   # evaluated, not yet promoted
    DISABLED = "disabled"
    ROLLED_BACK = "rolled_back"


class AgentVersion(Base):
    """One row per (agent_id, version) — supports rollback without data loss."""
    __tablename__ = "agent_versions"

    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String(50), nullable=False, index=True)   # e.g. "planner", "coding"
    version = Column(String(20), nullable=False)                 # e.g. "3.2"
    display_name = Column(String(100), nullable=False)

    model_provider = Column(String(20), nullable=False, default="ollama")  # ollama | openai
    model_name = Column(String(100), nullable=False)
    prompt_version = Column(String(20), nullable=True)
    tools = Column(JSON, nullable=True)             # list[str] of tool names this agent may call
    capabilities = Column(JSON, nullable=True)       # list[str] free-text capability tags

    status = Column(Enum(AgentStatus), nullable=False, default=AgentStatus.CANDIDATE)
    evaluation_score = Column(Float, nullable=True)  # 0.0-1.0, from the evaluator agent
    is_current = Column(Boolean, nullable=False, default=False)  # only one True per agent_id

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    activated_at = Column(DateTime(timezone=True), nullable=True)
    rolled_back_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "version": self.version,
            "display_name": self.display_name,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "prompt_version": self.prompt_version,
            "tools": self.tools or [],
            "capabilities": self.capabilities or [],
            "status": self.status.value if self.status else None,
            "evaluation_score": self.evaluation_score,
            "is_current": self.is_current,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
        }
