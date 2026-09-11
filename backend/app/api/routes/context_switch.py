from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from app.ai.ambient.context_switcher import context_switcher

router = APIRouter(prefix="/context", tags=["context-switching"])

class ProjectContextResponse(BaseModel):
    project_name: str
    last_active: str
    active_files: List[str]
    recent_topics: List[str]
    pending_tasks: List[dict]
    session_ids: List[str]
    parked_at: Optional[str] = None
    summary: str = ""

@router.get("/current", response_model=Optional[str])
async def get_current_context():
    return context_switcher.get_current_project()

@router.get("/projects", response_model=List[ProjectContextResponse])
async def get_active_projects(hours: int = 72):
    contexts = context_switcher.get_active_projects(hours)
    return [c.to_dict() for c in contexts]

@router.post("/switch/{project_name}", response_model=ProjectContextResponse)
async def switch_to_project(project_name: str):
    ctx = context_switcher.switch_to(project_name)
    return ctx.to_dict()

@router.post("/park", response_model=ProjectContextResponse)
async def park_current_context():
    ctx = context_switcher.park_current()
    if not ctx:
        raise HTTPException(status_code=400, detail="No active project to park")
    return ctx.to_dict()

@router.get("/parked", response_model=List[ProjectContextResponse])
async def get_parked_contexts():
    return [c.to_dict() for c in context_switcher.contexts.values() if c.parked_at is not None]
