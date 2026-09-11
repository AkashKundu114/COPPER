from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.ai.ambient.skill_learner import skill_learner

router = APIRouter(prefix="/skills", tags=["skills"])

class ExtractRequest(BaseModel):
    task_description: str
    steps: List[Dict[str, Any]]
    result: Dict[str, Any]

class ExecuteRequest(BaseModel):
    params: Dict[str, Any]

@router.get("")
async def list_skills(tag: Optional[str] = None):
    return skill_learner.list_skills(tag)

@router.get("/stats")
async def get_stats():
    return skill_learner.get_stats()

@router.get("/match")
async def match_skill(description: str = Query(...)):
    skill = skill_learner.find_matching_skill(description)
    if not skill:
        raise HTTPException(status_code=404, detail="No matching skill found")
    return skill

@router.get("/{skill_id}")
async def get_skill(skill_id: str):
    skill = skill_learner.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill

@router.post("/extract")
async def extract_skill(request: ExtractRequest):
    return skill_learner.extract_skill(
        task_description=request.task_description,
        steps_executed=request.steps,
        result=request.result
    )

@router.post("/{skill_id}/execute")
async def execute_skill(skill_id: str, request: ExecuteRequest):
    try:
        return await skill_learner.execute_skill(skill_id, request.params)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{skill_id}")
async def delete_skill(skill_id: str):
    success = skill_learner.delete_skill(skill_id)
    if not success:
        raise HTTPException(status_code=404, detail="Skill not found")
    return {"status": "success"}
