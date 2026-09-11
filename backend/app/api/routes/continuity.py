from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from app.ai.companion.context_continuity import context_continuity, SessionHandoff

router = APIRouter()

class HandoffSnapshotRequest(BaseModel):
    session_id: str
    project: str
    decisions: List[str]
    topics: List[str]
    next_steps: List[str]
    summary: str


@router.get("/latest", response_model=Optional[SessionHandoff])
async def get_latest_handoff(project: Optional[str] = None):
    return context_continuity.get_latest_handoff(project)


@router.post("/snapshot", response_model=SessionHandoff)
async def save_snapshot(request: HandoffSnapshotRequest):
    handoff = context_continuity.create_handoff(
        session_id=request.session_id,
        project=request.project,
        decisions=request.decisions,
        topics=request.topics,
        next_steps=request.next_steps,
        summary=request.summary,
    )
    return handoff


@router.get("/resume-prompt")
async def get_resume_prompt():
    prompt = context_continuity.generate_resume_prompt()
    return {"prompt": prompt}
