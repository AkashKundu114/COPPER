from fastapi import APIRouter

from app.ai.llm.model_tier_manager import model_tier_manager
from app.services.wake_word_service import wake_word_service

router = APIRouter(prefix="/voice/wake", tags=["wake-word"])


@router.get("/status")
async def wake_status():
    return {
        **wake_word_service.status(),
        "tier_manager": model_tier_manager.status(),
    }


@router.post("/enable")
async def wake_enable():
    return await wake_word_service.enable()


@router.post("/disable")
async def wake_disable():
    return await wake_word_service.disable()
