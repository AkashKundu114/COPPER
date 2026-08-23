from app.core.config import settings
from app.core.logger import logger

redis_client = None
try:
    import redis.asyncio as aioredis

    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    redis_client = aioredis.from_url(redis_url, decode_responses=True)
except Exception as e:
    logger.warning(f"Redis client disabled or unavailable (local memory fallback active): {e}")

async def get_redis():
    return redis_client

async def redis_close():
    if redis_client:
        try:
            await redis_client.close()
        except Exception:
            pass
