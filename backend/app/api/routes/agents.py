from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models.agent_registry import AgentStatus, AgentVersion
from app.database.postgres import get_db
from app.services.guardian_service import guardian_service

router = APIRouter(prefix="/agents", tags=["agents"])

class ActivateRequest(BaseModel):
    version_id: int

class HealthCheckRequest(BaseModel):
    version_id: int

@router.get("/")
async def list_agents(db: Session = Depends(get_db)):
    current = db.query(AgentVersion).filter(AgentVersion.is_current == True).all()
    if current:
        return [a.to_dict() for a in current]
    return [a.to_dict() for a in db.query(AgentVersion).all()]

@router.get("/{agent_id}/versions")
async def get_versions(agent_id: str, db: Session = Depends(get_db)):
    versions = (
        db.query(AgentVersion).filter(AgentVersion.agent_id == agent_id).order_by(AgentVersion.created_at.desc()).all()
    )
    return [v.to_dict() for v in versions]

@router.post("/{agent_id}/health-check")
async def health_check(agent_id: str, req: HealthCheckRequest, db: Session = Depends(get_db)):
    version = db.query(AgentVersion).filter(AgentVersion.id == req.version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    passed = version.status != AgentStatus.DISABLED
    return {"passed": passed, "agent_id": agent_id, "version_id": req.version_id}

@router.post("/{agent_id}/activate")
async def activate(agent_id: str, req: ActivateRequest, db: Session = Depends(get_db)):
    candidate = db.query(AgentVersion).filter(AgentVersion.id == req.version_id).first()
    if not candidate or candidate.agent_id != agent_id:
        raise HTTPException(status_code=404, detail="Version not found for this agent")
    current = db.query(AgentVersion).filter(AgentVersion.agent_id == agent_id, AgentVersion.is_current == True).first()
    if current:
        current.is_current = False
    candidate.is_current = True
    candidate.status = AgentStatus.ACTIVE
    candidate.activated_at = datetime.now(UTC)
    db.commit()
    guardian_service.log(
        db=db,
        category="agent_activated",
        actor="user",
        summary=f"Activated {agent_id} v{candidate.version} (from v{(current.version if current else 'none')})",
    )
    return candidate.to_dict()

@router.post("/{agent_id}/rollback")
async def rollback(agent_id: str, db: Session = Depends(get_db)):
    current = db.query(AgentVersion).filter(AgentVersion.agent_id == agent_id, AgentVersion.is_current == True).first()
    previous = (
        db.query(AgentVersion)
        .filter(AgentVersion.agent_id == agent_id, AgentVersion.status == AgentStatus.ACTIVE)
        .filter(AgentVersion.id != (current.id if current else -1))
        .order_by(AgentVersion.activated_at.desc())
        .first()
    )
    if not previous:
        raise HTTPException(status_code=404, detail="No previous version to roll back to")
    if current:
        current.is_current = False
        current.status = AgentStatus.ROLLED_BACK
        current.rolled_back_at = datetime.now(UTC)
    previous.is_current = True
    db.commit()
    guardian_service.log(
        db=db,
        category="agent_rolled_back",
        actor="user",
        summary=f"Rolled back {agent_id} from v{(current.version if current else '?')} to v{previous.version}",
    )
    return previous.to_dict()

@router.post("/{agent_id}/disable")
async def disable(agent_id: str, db: Session = Depends(get_db)):
    current = db.query(AgentVersion).filter(AgentVersion.agent_id == agent_id, AgentVersion.is_current == True).first()
    if not current:
        raise HTTPException(status_code=404, detail="No active version for this agent")
    current.status = AgentStatus.DISABLED
    current.is_current = False
    db.commit()
    guardian_service.log(
        db=db, category="agent_disabled", actor="user", summary=f"Disabled {agent_id} (v{current.version})"
    )
    return {"disabled": True, "agent_id": agent_id}
