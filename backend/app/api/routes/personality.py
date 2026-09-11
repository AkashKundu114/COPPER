from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.ai.companion.personality_manager import personality_manager

router = APIRouter(prefix="/personality", tags=["personality"])

class PersonalityUpdateRequest(BaseModel):
    warmth: Optional[float] = None
    formality: Optional[float] = None
    verbosity: Optional[float] = None
    humor: Optional[float] = None
    use_emojis: Optional[bool] = None
    code_first: Optional[bool] = None
    custom_instructions: Optional[List[str]] = None

@router.get("/config")
async def get_config():
    return personality_manager.config

@router.post("/config")
async def update_config(request: PersonalityUpdateRequest):
    update_data = request.model_dump(exclude_unset=True)
    personality_manager.update_config(**update_data)
    return {"status": "success", "config": personality_manager.config}

@router.get("/prompt-addon")
async def get_prompt_addon():
    return {"prompt_addon": personality_manager.get_system_prompt_addon()}
