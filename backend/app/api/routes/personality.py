from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.companion.personality_manager import personality_manager

router = APIRouter(prefix="/personality", tags=["personality"])


class PersonalityUpdateRequest(BaseModel):
    warmth: float | None = None
    formality: float | None = None
    verbosity: float | None = None
    humor: float | None = None
    use_emojis: bool | None = None
    code_first: bool | None = None
    custom_instructions: list[str] | None = None


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
