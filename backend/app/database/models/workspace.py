import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Column, DateTime, String

from app.database.postgres import Base


class WorkspaceItem(Base):
    """A small durable store for personal-OS records used by the UI."""

    __tablename__ = "workspace_items"

    id = Column(String(64), primary_key=True, default=lambda: str(uuid.uuid4()))
    kind = Column(String(32), nullable=False, index=True)
    payload = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            **(self.payload or {}),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
