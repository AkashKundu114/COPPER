from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.ai.companion.accountability_tracker import accountability_tracker

router = APIRouter(prefix="/accountability", tags=["accountability"])

class CommitmentCreate(BaseModel):
    title: str
    deadline: str
    urgency: Optional[str] = "medium"

@router.get("/commitments")
async def list_commitments():
    return [c.__dict__ for c in accountability_tracker.commitments]

@router.post("/commitments")
async def add_commitment(req: CommitmentCreate):
    c = accountability_tracker.add_commitment(req.title, req.deadline, req.urgency)
    return c.__dict__

@router.post("/commitments/{commitment_id}/fulfill")
async def fulfill_commitment(commitment_id: str):
    c = accountability_tracker.fulfill_commitment(commitment_id)
    if not c:
        raise HTTPException(status_code=404, detail="Commitment not found")
    return c.__dict__

@router.get("/report")
async def get_report():
    return accountability_tracker.get_accountability_report()

@router.post("/check-overdue")
async def check_overdue():
    return accountability_tracker.check_overdue_commitments()
