from typing import Any
from dataclasses import asdict
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.ai.os_integration.device_sync import device_sync
from app.ai.memory.epistemic_p2p_sync import epistemic_sync_coordinator, EncryptedSyncPayload
from app.ai.memory.crdt_sync import p2p_sync_engine
from app.core.logger import logger

router = APIRouter(prefix="/sync", tags=["device-sync"])


class PairDeviceRequest(BaseModel):
    device_id: str = Field(..., description="Unique device identifier to pair with")
    shared_secret_hex: str = Field(..., description="64-character hex pre-shared 256-bit AES key")


class ExportSyncRequest(BaseModel):
    recipient_device_id: str = Field(..., description="Target paired device identifier")


class IngestSyncRequest(BaseModel):
    payload_id: str
    sender_device_id: str
    recipient_device_id: str
    nonce_b64: str
    ciphertext_b64: str
    signature: str
    timestamp: float
    mutations_count: int


@router.post("/handoff")
async def generate_handoff():
    try:
        payload = device_sync.generate_handoff_payload()
        return asdict(payload)
    except Exception as e:
        logger.error(f"Error generating handoff: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/receive")
async def receive_handoff(payload: dict[str, Any]):
    try:
        result = device_sync.receive_handoff_payload(payload)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error receiving handoff: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/status")
async def get_sync_status():
    try:
        return device_sync.get_sync_status()
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# --- End-to-End Encrypted Epistemic Memory P2P Sync ---

@router.post("/epistemic/pair")
async def pair_epistemic_device(req: PairDeviceRequest):
    """Pairs a peer device with pre-shared AES-256-GCM symmetric key."""
    try:
        epistemic_sync_coordinator.pair_device(req.device_id, req.shared_secret_hex)
        return {
            "status": "success",
            "message": f"Device '{req.device_id}' successfully paired for E2EE epistemic sync.",
            "local_device_id": epistemic_sync_coordinator.local_device_id,
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error pairing device: {e}")
        raise HTTPException(status_code=500, detail="Failed to pair device")


@router.post("/epistemic/export")
async def export_epistemic_delta(req: ExportSyncRequest):
    """Exports encrypted and HMAC-signed epistemic CRDT delta for a paired device."""
    try:
        payload = epistemic_sync_coordinator.export_encrypted_delta(req.recipient_device_id)
        return payload.to_dict()
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        logger.error(f"Error exporting epistemic delta: {e}")
        raise HTTPException(status_code=500, detail="Failed to export epistemic delta")


@router.post("/epistemic/ingest")
async def ingest_epistemic_delta(req: IngestSyncRequest):
    """Validates, decrypts, and applies an incoming peer epistemic memory delta."""
    try:
        result = epistemic_sync_coordinator.ingest_encrypted_delta(req.model_dump())
        return result
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Error ingesting epistemic delta: {e}")
        raise HTTPException(status_code=500, detail="Failed to ingest epistemic delta")


@router.get("/epistemic/stats")
async def get_epistemic_sync_stats():
    """Returns local CRDT memory stats and sync counters."""
    return {
        "local_device_id": epistemic_sync_coordinator.local_device_id,
        "sync_stats": p2p_sync_engine.sync_stats,
        "total_active_facts": len(p2p_sync_engine.memory_crdt.read_all()),
    }
