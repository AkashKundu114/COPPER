from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.training.adapter_manager import adapter_manager
from app.ai.training.data_curator import data_curator
from app.ai.training.lora_trainer import lora_trainer
from app.core.logger import logger

router = APIRouter(prefix="/training", tags=["Training & Adapters (CHRYSALIS)"])


class StartTrainingRequest(BaseModel):
    base_model: str = Field(default="llama3.1:8b", description="Base model to fine-tune")
    target_agent: str = Field(default="all", description="Target agent specialization")


class ABTestRequest(BaseModel):
    percentage: int = Field(default=20, ge=1, le=99, description="Percentage of traffic to route to adapter")


class CurateRequest(BaseModel):
    min_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Minimum overall evaluation score to curate")
    limit: int = Field(default=50, ge=1, le=500, description="Maximum evaluations to inspect")


@router.get("/stats")
async def get_curation_stats() -> dict[str, Any]:
    """Retrieves dataset curation statistics, difficulty breakdown, and agent distribution."""
    try:
        return data_curator.get_curation_stats()
    except Exception as e:
        logger.error(f"Failed to fetch training stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/curate")
async def trigger_curation(req: CurateRequest = CurateRequest()) -> dict[str, Any]:
    """Manually triggers CHRYSALIS curation scan over recent CRUCIBLE response evaluations."""
    try:
        res = await data_curator.curate_from_evaluations(min_score=req.min_score, limit=req.limit)
        return {"status": "success", "result": res}
    except Exception as e:
        logger.error(f"Failed during data curation run: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_training(req: StartTrainingRequest = StartTrainingRequest()) -> dict[str, Any]:
    """Initiates an on-device QLoRA fine-tuning run with GPU VRAM clearing and regression testing."""
    try:
        res = await lora_trainer.start_training(base_model=req.base_model, target_agent=req.target_agent)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("error", "Training start failed"))
        return {"status": "success", "job": res}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to initiate training: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_training_status(job_id: int | None = None) -> dict[str, Any]:
    """Retrieves progress and metrics of the current or specified training job."""
    try:
        job = lora_trainer.get_job_status(job_id)
        if not job:
            return {"status": "idle", "message": "No training runs recorded."}
        return {"status": "success", "job": job}
    except Exception as e:
        logger.error(f"Failed to fetch training status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/adapters")
async def list_adapters() -> list[dict[str, Any]]:
    """Lists all registered LoRA adapters with their versions, status, and benchmark results."""
    try:
        return adapter_manager.get_all_adapters()
    except Exception as e:
        logger.error(f"Failed to list adapters: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adapters/{adapter_id}/activate")
async def activate_adapter(adapter_id: int) -> dict[str, Any]:
    """Activates an adapter for 100% of traffic, deactivating prior models for that agent."""
    try:
        res = adapter_manager.activate_adapter(adapter_id)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to activate adapter"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate adapter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adapters/{adapter_id}/deactivate")
async def deactivate_adapter(adapter_id: int) -> dict[str, Any]:
    """Deactivates an adapter and rolls back to base weights."""
    try:
        res = adapter_manager.deactivate_adapter(adapter_id)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to deactivate adapter"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate adapter: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adapters/{adapter_id}/ab-test")
async def start_ab_test(adapter_id: int, req: ABTestRequest = ABTestRequest()) -> dict[str, Any]:
    """Routes N% of live traffic to the adapted model for empirical A/B testing."""
    try:
        res = adapter_manager.start_ab_test(adapter_id, percentage=req.percentage)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to configure A/B test"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/adapters/{adapter_id}/merge")
async def merge_adapter(adapter_id: int) -> dict[str, Any]:
    """Merges LoRA adapter weights into base model weights after stability verification."""
    try:
        res = adapter_manager.merge_adapter(adapter_id)
        if not res.get("success"):
            raise HTTPException(status_code=400, detail=res.get("error", "Failed to merge adapter"))
        return res
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to merge adapter: {e}")
        raise HTTPException(status_code=500, detail=str(e))
