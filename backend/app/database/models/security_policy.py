from sqlalchemy import JSON, Boolean, Column, DateTime, String
from sqlalchemy.sql import func

from app.database.postgres import Base


class SecurityPolicy(Base):
    __tablename__ = "security_policies"

    id = Column(String(64), primary_key=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    policy_type = Column(String(50), nullable=False, default="rbac")
    definition = Column(JSON, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "policy_type": self.policy_type,
            "definition": self.definition,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
