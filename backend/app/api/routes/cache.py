from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.ai.cache.semantic_cache import semantic_cache
from app.core.logger import logger

router = APIRouter(prefix="/cache", tags=["cache"])


class CacheClearResponse(BaseModel):
    status: str
    message: str
    cleared_entries: int


@router.get("/stats")
async def get_cache_stats():
    """
    Retrieves semantic response cache telemetry and performance statistics:
    hit rate, size, hits/misses/hints, and average inference latency savings.
    """
    try:
        stats = await semantic_cache.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching cache stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clear", response_model=CacheClearResponse)
async def clear_cache():
    """
    Clears the ChromaDB response cache collection and resets in-memory/Redis counters.
    """
    try:
        cleared_count = await semantic_cache.clear()
        logger.info(f"Semantic response cache cleared ({cleared_count} items removed).")
        return CacheClearResponse(
            status="success",
            message="Semantic response cache cleared successfully.",
            cleared_entries=cleared_count,
        )
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))
