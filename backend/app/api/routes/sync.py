from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.ai.os_integration.device_sync import device_sync
from app.core.logger import logger

router = APIRouter(prefix="/sync", tags=["device-sync"])

@router.post("/handoff")
async def generate_handoff():
    try:
        payload = device_sync.generate_handoff_payload()
        from dataclasses import asdict
        return asdict(payload)
    except Exception as e:
        logger.error(f"Error generating handoff: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/receive")
async def receive_handoff(payload: Dict[str, Any]):
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
