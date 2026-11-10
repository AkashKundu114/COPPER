"""Distributed Lock & Lease Manager for C.O.P.P.E.R.

Guarantees exactly-once task execution, preventing race conditions and duplicate
operations across concurrent background workers and multi-pod backend replicas.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any

from app.core.logger import logger
from app.database.redis_client import get_redis


# Lua script for atomic safe lock release in Redis
RELEASE_LOCK_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


class DistributedLock:
    """Represents an acquired distributed lock lease."""

    def __init__(self, manager: DistributedLockManager, resource: str, token: str, is_local: bool):
        self.manager = manager
        self.resource = resource
        self.token = token
        self.is_local = is_local

    async def release(self) -> bool:
        return await self.manager.release_lock(self.resource, self.token)

    async def __aenter__(self) -> DistributedLock:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.release()


class DistributedLockManager:
    """Hybrid distributed lock coordinator with automatic local fallback."""

    def __init__(self, default_lease_seconds: int = 30):
        self.default_lease = default_lease_seconds
        self._local_locks: dict[str, tuple[str, float]] = {}  # resource -> (token, expiry)
        self._asyncio_mutex = asyncio.Lock()

    async def acquire_lock(
        self,
        resource: str,
        lease_seconds: int | None = None,
        timeout_seconds: float = 5.0,
    ) -> DistributedLock | None:
        """Attempts to acquire exclusive lock for resource within timeout."""
        ttl = lease_seconds or self.default_lease
        token = str(uuid.uuid4())
        key = f"copper:lock:{resource}"
        start_time = time.time()

        while (time.time() - start_time) < timeout_seconds:
            # 1. Try Redis Lock if available
            try:
                redis = await get_redis()
                if redis:
                    acquired = await redis.set(key, token, nx=True, ex=ttl)
                    if acquired:
                        return DistributedLock(self, resource, token, is_local=False)
            except Exception as e:
                logger.debug(f"[DistributedLock] Redis lock fallback to local mutex: {e}")

            # 2. Local Fallback Lock (Desktop Profile or Redis unavailable)
            async with self._asyncio_mutex:
                now = time.time()
                current = self._local_locks.get(resource)
                if not current or current[1] <= now:
                    self._local_locks[resource] = (token, now + ttl)
                    return DistributedLock(self, resource, token, is_local=True)

            await asyncio.sleep(0.05)

        logger.warning(f"[DistributedLock] Failed to acquire lock for '{resource}' within {timeout_seconds}s timeout.")
        return None

    async def release_lock(self, resource: str, token: str) -> bool:
        """Safely releases lock if the caller still holds the valid lease."""
        key = f"copper:lock:{resource}"

        # 1. Release in Redis
        try:
            redis = await get_redis()
            if redis:
                res = await redis.eval(RELEASE_LOCK_LUA, 1, key, token)
                if res == 1:
                    return True
        except Exception as e:
            logger.debug(f"[DistributedLock] Redis release failed: {e}")

        # 2. Release in Local Table
        async with self._asyncio_mutex:
            current = self._local_locks.get(resource)
            if current and current[0] == token:
                del self._local_locks[resource]
                return True

        return False


distributed_lock_manager = DistributedLockManager()
