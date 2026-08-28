from fastapi import APIRouter, Query, HTTPException
from typing import Optional

from app.services.self_model_service import self_model_service

router = APIRouter(prefix="/self-memory", tags=["self-memory"])

@router.get("")
async def get_self_memories(
    category: Optional[str] = Query(None, description="Filter by self memory category"),
    limit: int = Query(50, description="Max number of entries to return")
):
    entries = self_model_service.get_all(category=category, limit=limit)
    return {"data": entries}

@router.post("/{memory_id}/resolve")
async def resolve_self_memory(memory_id: str):
    success = self_model_service.resolve(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory entry not found or update failed")
    return {"status": "success", "message": "Memory resolved"}
