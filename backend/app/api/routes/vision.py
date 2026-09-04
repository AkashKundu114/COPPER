from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.agents.vision_agent import vision_agent
from app.ai.tools.builtin import screen_tools
from app.services.vision_service import vision_service

router = APIRouter(prefix="/vision", tags=["vision"])


class ComputerUseRequest(BaseModel):
    goal: str
    session_id: str | None = None


class FrameObservationRequest(BaseModel):
    image_base64: str
    source: str = "camera"  # "camera" or "screen"


@router.get("/status")
async def vision_status():
    w, h = screen_tools.get_screen_size()
    active_win = screen_tools.get_active_window_title()
    return {
        "status": "ready",
        "agent": vision_agent.name,
        "vision_model": vision_agent.get_target_model(),
        "grounding_model": vision_agent.get_grounding_model(),
        "screen_resolution": f"{w}x{h}",
        "active_window": active_win,
        "tools": vision_agent.tools,
    }


@router.post("/screenshot")
async def take_screenshot(max_dimension: int = 1920):
    result = await screen_tools.screenshot(max_dimension=max_dimension)
    if result.get("status") == "error":
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/execute")
async def execute_task(req: ComputerUseRequest):
    try:
        report = await vision_agent.run(req.goal, session_id=req.session_id)
        return {
            "status": "success",
            "goal": req.goal,
            "report": report,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/observe")
async def observe_frame(req: FrameObservationRequest):
    """
    Receives base64 webcam or screen frame snapshot, runs local optical inference,
    and returns a concise contextual observation.
    """
    try:
        result = await vision_service.observe_frame(req.image_base64, source=req.source)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

