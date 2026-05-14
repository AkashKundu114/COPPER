import json
from typing import Any, Optional
import redis.asyncio as aioredis
from app.core.config import settings
from app.core.logger import logger

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def redis_set(key: str, value: Any, ttl: int = 3600) -> bool:
    try:
        r = await get_redis()
        return await r.setex(key, ttl, json.dumps(value))
    except Exception as e:
        logger.error(f"Redis set error: {e}")
        return False


async def redis_get(key: str) -> Optional[Any]:
    try:
        r = await get_redis()
        data = await r.get(key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Redis get error: {e}")
        return None


async def redis_delete(key: str) -> bool:
    try:
        r = await get_redis()
        return bool(await r.delete(key))
    except Exception as e:
        logger.error(f"Redis delete error: {e}")
        return False


async def redis_close():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
