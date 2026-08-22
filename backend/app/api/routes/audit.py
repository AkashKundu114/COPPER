import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.database.models.audit_log import AuditLogEntry
from app.database.models.history import ChatHistory
from app.database.models.memory_v2 import UserMemoryV2
from app.database.postgres import get_db

router = APIRouter(prefix="/audit", tags=["audit"])


class DeleteAllRequest(BaseModel):
    confirm: bool


@router.get("/")
async def list_audit(category: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    q = db.query(AuditLogEntry)
    if category:
        q = q.filter(AuditLogEntry.category == category)
    entries = q.order_by(AuditLogEntry.created_at.desc()).limit(limit).all()
    return [e.to_dict() for e in entries]


@router.get("/export")
async def export_data(db: Session = Depends(get_db)):
    payload = {
        "audit_log": [e.to_dict() for e in db.query(AuditLogEntry).all()],
        "memories": [m.to_dict() for m in db.query(UserMemoryV2).all()],
        "chat_history": [c.to_dict() for c in db.query(ChatHistory).all()],
    }
    body = json.dumps(payload, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=copper-data-export.json"},
    )


@router.post("/delete-all")
async def delete_all_data(req: DeleteAllRequest, db: Session = Depends(get_db)):
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required")
    deleted = {
        "audit_log": db.query(AuditLogEntry).delete(),
        "memories": db.query(UserMemoryV2).delete(),
        "chat_history": db.query(ChatHistory).delete(),
    }
    db.commit()
    logger.warning(f"User requested full data deletion: {deleted}")
    return {"deleted": True, "counts": deleted}
