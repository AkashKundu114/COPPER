"""
Image Generation API endpoints for C.O.P.P.E.R. Local PICASSO Studio.
"""

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.image.diffusion_engine import diffusion_engine

router = APIRouter(prefix="/images", tags=["images"])


class ImageGenerateRequest(BaseModel):
    prompt: str = Field(..., description="Text prompt describing the desired image")
    width: Optional[int] = Field(512, ge=256, le=1024, description="Image width")
    height: Optional[int] = Field(512, ge=256, le=1024, description="Image height")
    steps: Optional[int] = Field(1, ge=1, le=50, description="Inference steps")
    seed: Optional[int] = Field(None, description="Random seed for deterministic generation")


@router.get("/status")
async def get_image_engine_status():
    """Get diagnostic status of local diffusion engine and model weights."""
    return diffusion_engine.get_status()


@router.post("/generate")
async def generate_image(request: ImageGenerateRequest):
    """Generate an image using the local 100% offline diffusion engine."""
    try:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None,
            diffusion_engine.generate,
            request.prompt,
            request.width,
            request.height,
            request.steps,
            request.seed,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image generation error: {str(e)}")


@router.post("/unload")
async def unload_image_engine():
    """Unload diffusion pipeline from GPU VRAM back into system memory."""
    unloaded = diffusion_engine.unload()
    return {"unloaded": unloaded, "status": "VRAM reclaimed"}
