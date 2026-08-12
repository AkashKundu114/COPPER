"""
Audit log — human-readable event trail. Master UI Prompt §21.
Rule: NEVER store secrets, API keys, tokens, or raw credentials here.
Callers must redact before calling `log_event` (see services/audit_service.py).
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database.postgres import Base

# Event categories shown in the Security Center audit view.
CATEGORY_CHOICES = (
    "agent_activated", "agent_replaced", "agent_rolled_back",
    "tool_executed", "external_api_accessed",
    "memory_created", "memory_deleted", "memory_rejected",
    "data_export_requested", "data_deleted",
    "security_setting_changed", "guardian_challenge", "guardian_safety_block",
)


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)

    category = Column(String(50), nullable=False, index=True)
    actor = Column(String(50), nullable=False)     # agent_id or "user" or "system"
    summary = Column(String(300), nullable=False)  # short human-readable line
    detail = Column(Text, nullable=True)            # optional longer description
    scope = Column(String(20), nullable=False, default="local")  # "local" | "cloud"

    extra_metadata = Column("metadata", JSON, nullable=True)  # non-sensitive structured extras
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "actor": self.actor,
            "summary": self.summary,
            "detail": self.detail,
            "scope": self.scope,
            "metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
