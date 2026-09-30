"""
FastAPI REST endpoints for COPPER GPU hardware activation and licensing.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.gpu_activation import (
    activate_local_gpu,
    activate_with_owner_code,
    generate_fingerprint,
    is_activated,
    load_activation,
    revoke_activation,
)

router = APIRouter(prefix="/api/activation", tags=["activation"])


class OwnerCodeRequest(BaseModel):
    code: str = Field(..., description="The owner's shared master activation code", min_length=4)


@router.get("/status", summary="Check current activation status")
def get_activation_status() -> dict[str, Any]:
    """Returns the current activation state, mode, and detected GPU."""
    state = load_activation()
    fp = generate_fingerprint()
    return {
        "activated": state.activated,
        "mode": state.mode,
        "activation_code": state.activation_code if state.activated else None,
        "system_fingerprint_code": fp.activation_code,
        "gpu_info": {
            "name": fp.gpu_name,
            "vram_mb": fp.gpu_vram_mb,
            "is_dedicated": fp.gpu_vram_mb > 1024,
        },
    }


@router.get("/fingerprint", summary="Get system hardware fingerprint")
def get_system_fingerprint() -> dict[str, Any]:
    """Returns host hardware information and candidate local activation code."""
    fp = generate_fingerprint()
    return {
        "activation_code": fp.activation_code,
        "fingerprint_hash": fp.fingerprint_hash,
        "gpu_name": fp.gpu_name,
        "gpu_vram_mb": fp.gpu_vram_mb,
        "cpu_name": fp.cpu_name,
        "machine_id": fp.machine_id,
        "os_type": fp.os_type,
    }


@router.post("/activate/local", summary="Activate using local GPU hardware")
def activate_local() -> dict[str, Any]:
    """Activates the app bound to the local system GPU/hardware."""
    state = activate_local_gpu()
    return {
        "success": True,
        "activated": state.activated,
        "mode": state.mode,
        "activation_code": state.activation_code,
        "gpu_info": state.gpu_info,
    }


@router.post("/activate/owner-code", summary="Activate using owner's master code")
def activate_owner(req: OwnerCodeRequest) -> dict[str, Any]:
    """Authorizes execution using the owner's shared access code."""
    state = activate_with_owner_code(req.code)
    if not state.activated:
        raise HTTPException(
            status_code=401,
            detail="Invalid activation code. Please check with the repository owner for an authorized code.",
        )
    return {
        "success": True,
        "activated": state.activated,
        "mode": state.mode,
        "activation_code": state.activation_code,
    }


@router.post("/revoke", summary="Revoke current activation")
def revoke() -> dict[str, Any]:
    """Revokes the current activation file on disk."""
    success = revoke_activation()
    return {"success": success, "activated": is_activated()}
