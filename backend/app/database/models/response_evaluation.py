from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database.postgres import Base


class FailureCategory(str, PyEnum):
    HALLUCINATION = "HALLUCINATION"
    WRONG_AGENT = "WRONG_AGENT"
    INCOMPLETE = "INCOMPLETE"
    VERBOSE = "VERBOSE"
    GENERIC = "GENERIC"
    SAFETY_FALSE_POSITIVE = "SAFETY_FALSE_POSITIVE"
    TOOL_MISUSE = "TOOL_MISUSE"
    NONE = "NONE"


class EditStatus(str, PyEnum):
    PENDING = "pending"
    APPLIED = "applied"
    REJECTED = "rejected"


class ResponseEvaluation(Base):
    __tablename__ = "response_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    agent_type = Column(String(50), nullable=False, default="chat", index=True)
    model_name = Column(String(100), nullable=True, default="default", index=True)
    latency_ms = Column(Float, nullable=True, default=0.0)
    accuracy = Column(Float, nullable=False, default=1.0)
    relevance = Column(Float, nullable=False, default=1.0)
    completeness = Column(Float, nullable=False, default=1.0)
    helpfulness = Column(Float, nullable=False, default=1.0)
    voice_consistency = Column(Float, nullable=False, default=1.0)
    overall_score = Column(Float, nullable=False, default=1.0)
    failures = Column(JSON, nullable=False, default=list)
    reasoning = Column(Text, nullable=False, default="")
    improvement_suggestion = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "agent_type": self.agent_type,
            "model_name": self.model_name,
            "latency_ms": round(self.latency_ms or 0.0, 1),
            "scores": {
                "accuracy": round(self.accuracy, 2),
                "relevance": round(self.relevance, 2),
                "completeness": round(self.completeness, 2),
                "helpfulness": round(self.helpfulness, 2),
                "voice_consistency": round(self.voice_consistency, 2),
            },
            "overall_score": round(self.overall_score, 2),
            "failures": self.failures or [],
            "reasoning": self.reasoning,
            "improvement_suggestion": self.improvement_suggestion,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ProposedPromptEdit(Base):
    __tablename__ = "proposed_prompt_edits"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    agent_type = Column(String(50), nullable=False, index=True)
    failure_category = Column(String(50), nullable=False)
    failure_count = Column(Integer, nullable=False, default=1)
    target_prompt_section = Column(String(100), nullable=False, default="instructions")
    current_prompt_snippet = Column(Text, nullable=True)
    proposed_prompt_snippet = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default=EditStatus.PENDING.value, index=True)
    benchmark_before_score = Column(Float, nullable=True)
    benchmark_after_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    applied_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "failure_category": self.failure_category,
            "failure_count": self.failure_count,
            "target_prompt_section": self.target_prompt_section,
            "current_prompt_snippet": self.current_prompt_snippet,
            "proposed_prompt_snippet": self.proposed_prompt_snippet,
            "rationale": self.rationale,
            "status": self.status,
            "benchmark_before_score": self.benchmark_before_score,
            "benchmark_after_score": self.benchmark_after_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "applied_at": self.applied_at.isoformat() if self.applied_at else None,
        }


class AgentModelPerformance(Base):
    __tablename__ = "agent_model_performance"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    agent_type = Column(String(50), nullable=False, index=True)
    model_name = Column(String(100), nullable=False, index=True)
    sample_count = Column(Integer, nullable=False, default=0)
    avg_quality_score = Column(Float, nullable=False, default=0.0)
    avg_latency_ms = Column(Float, nullable=False, default=0.0)
    failure_count = Column(Integer, nullable=False, default=0)
    is_active_route = Column(Boolean, nullable=False, default=False)
    last_evaluated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_type": self.agent_type,
            "model_name": self.model_name,
            "sample_count": self.sample_count,
            "avg_quality_score": round(self.avg_quality_score, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 1),
            "failure_count": self.failure_count,
            "is_active_route": self.is_active_route,
            "last_evaluated_at": self.last_evaluated_at.isoformat() if self.last_evaluated_at else None,
        }

