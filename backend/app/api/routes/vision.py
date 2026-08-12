from fastapi import APIRouter

router = APIRouter(prefix="/vision", tags=["vision"])


@router.get("/status")
async def vision_status():
    return {"status": "ready", "vision_model": "llava:7b"}
