"""Shared Session Store for Multi-Replica Deployments in C.O.P.P.E.R.

Provides distributed session state across backend pods and containers using Redis,
with transparent, zero-dependency local JSON file and in-memory fallback for desktop mode.
"""

from __future__ import annotations

import json
import time
from typing import Any

from app.core.logger import logger
from app.database.redis_client import get_redis


class SharedSessionStore:
    """Multi-replica session store with automatic local fallback."""

    def __init__(self, ttl_seconds: int = 86400 * 7):  # 7 days
        self.ttl_seconds = ttl_seconds
        self._local_sessions: dict[str, list[dict[str, Any]]] = {}

    async def append_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Appends a turn to the session history across distributed replicas."""
        message_entry = {
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "metadata": metadata or {},
        }

        # 1. Store in Redis if available (Homelab / Cluster profiles)
        try:
            redis = await get_redis()
            if redis:
                key = f"copper:session:{session_id}"
                await redis.rpush(key, json.dumps(message_entry))
                await redis.expire(key, self.ttl_seconds)
                logger.debug(f"[SharedSessionStore] Appended message to Redis session '{session_id}'")
                return message_entry
        except Exception as e:
            logger.debug(f"[SharedSessionStore] Redis session append failed, falling back to local: {e}")

        # 2. Local Fallback (Desktop profile)
        if session_id not in self._local_sessions:
            self._local_sessions[session_id] = []
        self._local_sessions[session_id].append(message_entry)
        return message_entry

    async def get_session_history(self, session_id: str, limit: int = 50) -> list[dict[str, Any]]:
        """Retrieves conversation history across replicas."""
        # 1. Try Redis
        try:
            redis = await get_redis()
            if redis:
                key = f"copper:session:{session_id}"
                raw_items = await redis.lrange(key, -limit, -1)
                if raw_items:
                    return [json.loads(item) for item in raw_items]
        except Exception as e:
            logger.debug(f"[SharedSessionStore] Redis session read failed: {e}")

        # 2. Local Fallback
        entries = self._local_sessions.get(session_id, [])
        return entries[-limit:]

    async def clear_session(self, session_id: str) -> bool:
        """Deletes session across stores."""
        cleared = False
        try:
            redis = await get_redis()
            if redis:
                await redis.delete(f"copper:session:{session_id}")
                cleared = True
        except Exception:
            pass

        if session_id in self._local_sessions:
            del self._local_sessions[session_id]
            cleared = True

        return cleared


shared_session_store = SharedSessionStore()
