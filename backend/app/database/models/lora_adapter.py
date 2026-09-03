from enum import Enum as PyEnum
from typing import Any

from sqlalchemy import JSON, Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.sql import func

from app.database.postgres import Base


class AdapterStatus(str, PyEnum):
    CANDIDATE = "candidate"
    ACTIVE = "active"
    TESTING = "testing"
    MERGED = "merged"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class TrainingJobStatus(str, PyEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ABORTED = "aborted"


class CuratedTrainingExample(Base):
    __tablename__ = "curated_training_examples"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False, default="chat", index=True)
    system_prompt = Column(Text, nullable=False)
    user_message = Column(Text, nullable=False)
    assistant_response = Column(Text, nullable=False)
    quality_score = Column(Float, nullable=False, default=1.0)
    difficulty = Column(String(20), nullable=False, default="medium")  # easy, medium, hard
    quality_tags = Column(JSON, nullable=False, default=list)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "system_prompt": self.system_prompt,
            "user_message": self.user_message,
            "assistant_response": self.assistant_response,
            "quality_score": round(self.quality_score, 2),
            "difficulty": self.difficulty,
            "quality_tags": self.quality_tags or [],
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class TrainingJob(Base):
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    version_tag = Column(String(50), nullable=False, unique=True, index=True)
    base_model = Column(String(100), nullable=False, default="llama3.1:8b")
    target_agent = Column(String(50), nullable=False, default="all")
    status = Column(String(20), nullable=False, default=TrainingJobStatus.PENDING.value, index=True)
    current_epoch = Column(Integer, nullable=False, default=0)
    total_epochs = Column(Integer, nullable=False, default=3)
    current_step = Column(Integer, nullable=False, default=0)
    total_steps = Column(Integer, nullable=False, default=0)
    train_loss = Column(Float, nullable=True)
    eval_loss = Column(Float, nullable=True)
    benchmark_routing_before = Column(Float, nullable=True)
    benchmark_routing_after = Column(Float, nullable=True)
    benchmark_guardian_before = Column(Float, nullable=True)
    benchmark_guardian_after = Column(Float, nullable=True)
    adapter_dir = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version_tag": self.version_tag,
            "base_model": self.base_model,
            "target_agent": self.target_agent,
            "status": self.status,
            "progress": {
                "current_epoch": self.current_epoch,
                "total_epochs": self.total_epochs,
                "current_step": self.current_step,
                "total_steps": self.total_steps,
            },
            "metrics": {
                "train_loss": round(self.train_loss, 4) if self.train_loss is not None else None,
                "eval_loss": round(self.eval_loss, 4) if self.eval_loss is not None else None,
            },
            "benchmark": {
                "routing_before": self.benchmark_routing_before,
                "routing_after": self.benchmark_routing_after,
                "guardian_before": self.benchmark_guardian_before,
                "guardian_after": self.benchmark_guardian_after,
            },
            "adapter_dir": self.adapter_dir,
            "error_message": self.error_message,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LoRAAdapter(Base):
    __tablename__ = "lora_adapters"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    version = Column(String(50), nullable=False, unique=True, index=True)
    adapter_dir = Column(String(255), nullable=False)
    base_model = Column(String(100), nullable=False, default="llama3.1:8b")
    target_agent = Column(String(50), nullable=False, default="all", index=True)
    status = Column(String(20), nullable=False, default=AdapterStatus.CANDIDATE.value, index=True)
    ab_test_percentage = Column(Integer, nullable=False, default=0)  # 0-100%
    evaluation_quality_score = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    training_loss = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    activated_at = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "adapter_dir": self.adapter_dir,
            "base_model": self.base_model,
            "target_agent": self.target_agent,
            "status": self.status,
            "ab_test_percentage": self.ab_test_percentage,
            "evaluation_quality_score": round(self.evaluation_quality_score, 2) if self.evaluation_quality_score is not None else None,
            "is_active": self.is_active,
            "training_loss": round(self.training_loss, 4) if self.training_loss is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "activated_at": self.activated_at.isoformat() if self.activated_at else None,
        }
