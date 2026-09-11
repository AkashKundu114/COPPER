from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.memory.differential_privacy import dp_engine

router = APIRouter(prefix="/privacy", tags=["differential-privacy"])

class ConfigureRequest(BaseModel):
    epsilon: float
    delta: float
    budget_limit: float

class NoiseDemoRequest(BaseModel):
    embedding: list[float]

@router.get("/budget")
async def get_budget():
    return dp_engine.get_budget_status()

@router.post("/configure")
async def configure_dp(req: ConfigureRequest):
    dp_engine.configure(epsilon=req.epsilon, delta=req.delta, budget_limit=req.budget_limit)
    return {"status": "success", "message": "DP configured successfully"}

@router.post("/reset")
async def reset_budget():
    dp_engine.reset_budget()
    return {"status": "success", "message": "Privacy budget reset"}

@router.get("/guarantee")
async def get_guarantee():
    return {"guarantee": dp_engine.get_privacy_guarantee()}

@router.post("/noise-demo")
async def noise_demo(req: NoiseDemoRequest):
    noised = dp_engine.add_noise_to_embedding(req.embedding)
    return {
        "original": req.embedding,
        "noised": noised
    }
