from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.postgres import get_db
from app.services.guardian_service import guardian_service

router = APIRouter(prefix="/guardian", tags=["guardian"])


class AcknowledgeRequest(BaseModel):
    session_id: str
    decision: str


class ConfirmRequest(BaseModel):
    session_id: str
    confirmation_text: str


@router.post("/acknowledge")
async def acknowledge(req: AcknowledgeRequest, db: Session = Depends(get_db)):
    if req.decision not in ("follow", "proceed", "discuss"):
        raise HTTPException(status_code=400, detail="Invalid decision")
    guardian_service.log(
        db=db,
        category="guardian_challenge",
        actor="user",
        summary=f"User chose '{req.decision}' on a Level 2 guardian challenge",
        session_id=req.session_id,
    )
    return {"acknowledged": True, "decision": req.decision}


@router.post("/confirm")
async def confirm_safety_action(req: ConfirmRequest, db: Session = Depends(get_db)):
    if req.confirmation_text.strip().lower() != "confirm":
        raise HTTPException(status_code=400, detail="Confirmation text did not match")
    guardian_service.log(
        db=db,
        category="guardian_safety_block",
        actor="user",
        summary="User explicitly confirmed a Level 3 safety-boundary action",
        session_id=req.session_id,
    )
    return {"confirmed": True}
