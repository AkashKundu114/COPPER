from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.memory.differential_privacy import dp_engine
from app.core.privacy.classification import GOVERNANCE_POLICIES
from app.core.privacy.governance_manager import data_governance_manager
from app.database.postgres import get_db

router = APIRouter(prefix="/privacy", tags=["privacy-and-governance"])


class ConfigureRequest(BaseModel):
    epsilon: float
    delta: float
    budget_limit: float


class NoiseDemoRequest(BaseModel):
    embedding: list[float]


class UserCorrectionRequest(BaseModel):
    memory_id: int
    new_content: str
    reason: str = "user_correction"


class VerifiableDeleteRequest(BaseModel):
    confirm: bool


class ConsentUpdateRequest(BaseModel):
    telemetry_collection: bool = True
    ambient_memory_recording: bool = True
    cloud_model_fallback: bool = False


# In-memory consent storage with defaults
_CONSENT_SETTINGS = {
    "telemetry_collection": True,
    "ambient_memory_recording": True,
    "cloud_model_fallback": False,
    "last_updated": "2026-11-10T00:00:00Z",
}


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
    return {"original": req.embedding, "noised": noised}


# ─── Data Governance & User Rights Endpoints ──────────────────────────────


@router.get("/policies")
async def list_governance_policies():
    """Returns access, retention, and processing rules for all 5 data classifications."""
    return {
        "standard": "COPPER Unified Data Governance",
        "classifications": {k.value: v.to_dict() for k, v in GOVERNANCE_POLICIES.items()},
    }


@router.get("/export")
async def export_user_data(db: Session = Depends(get_db)):
    """User Right: Complete portable data export with manifest and integrity checksum."""
    payload = data_governance_manager.export_comprehensive_user_data(db)
    import json
    body = json.dumps(payload, indent=2, default=str)
    return Response(
        content=body,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=copper-export-{payload['export_id'][:8]}.json"},
    )


@router.post("/correct")
async def correct_user_data(req: UserCorrectionRequest, db: Session = Depends(get_db)):
    """User Right: Corrects false, outdated, or inaccurate memory across stores."""
    try:
        result = await data_governance_manager.correct_user_memory(
            db=db,
            memory_id=req.memory_id,
            new_content=req.new_content,
            reason=req.reason,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Correction failed: {e}")


@router.post("/delete-all")
async def execute_verifiable_deletion(req: VerifiableDeleteRequest, db: Session = Depends(get_db)):
    """User Right: Executes complete cross-store verifiable deletion and issues cryptographic receipt."""
    if not req.confirm:
        raise HTTPException(status_code=400, detail="Confirmation required to execute deletion")

    receipt = await data_governance_manager.execute_verifiable_full_deletion(db=db, operator="user")
    return {
        "status": "deleted",
        "receipt": receipt.to_dict(),
    }


@router.post("/retention/enforce")
async def trigger_retention_enforcement(db: Session = Depends(get_db)):
    """Enforces TTL retention policies, removing expired personal, sensitive, and hypothesis data."""
    purged = data_governance_manager.enforce_retention_policies(db=db)
    return {
        "status": "enforced",
        "purged_records": purged,
    }


@router.get("/consent")
async def get_consent_settings():
    """Returns the current data processing consent settings."""
    return _CONSENT_SETTINGS


@router.post("/consent")
async def update_consent_settings(req: ConsentUpdateRequest):
    """Updates user consent settings for telemetry, ambient memory, and external fallbacks."""
    from datetime import UTC, datetime
    _CONSENT_SETTINGS["telemetry_collection"] = req.telemetry_collection
    _CONSENT_SETTINGS["ambient_memory_recording"] = req.ambient_memory_recording
    _CONSENT_SETTINGS["cloud_model_fallback"] = req.cloud_model_fallback
    _CONSENT_SETTINGS["last_updated"] = datetime.now(UTC).isoformat()
    return {
        "status": "updated",
        "consent": _CONSENT_SETTINGS,
    }
