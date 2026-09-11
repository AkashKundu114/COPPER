from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.ai.companion.skill_gap_detector import skill_gap_detector, SkillGap

router = APIRouter(prefix="/skill-gaps", tags=["skill-gaps"])

class RecordTopicRequest(BaseModel):
    topic: str

class UpdateStatusRequest(BaseModel):
    status: str

@router.get("", response_model=List[SkillGap])
async def list_skill_gaps():
    return skill_gap_detector.get_active_gaps()

@router.post("/record")
async def record_query_topic(req: RecordTopicRequest):
    skill_gap_detector.record_query_topic(req.topic)
    return {"status": "recorded", "topic": req.topic}

@router.patch("/{gap_id}")
async def update_gap_status(gap_id: str, req: UpdateStatusRequest):
    success = skill_gap_detector.mark_gap_status(gap_id, req.status)
    if not success:
        raise HTTPException(status_code=404, detail="Skill gap not found")
    return {"status": "updated", "gap_id": gap_id, "new_status": req.status}
