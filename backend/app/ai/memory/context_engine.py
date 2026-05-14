from typing import Optional
from app.ai.memory.memory_manager import memory_manager
from app.database.redis_client import redis_get, redis_set
from app.core.constants import CHAT_HISTORY_LIMIT
from app.core.logger import logger


class ContextEngine:
    SESSION_TTL = 86400  # 24 hours

    async def get_history(self, session_id: str) -> list[dict]:
        key = f"history:{session_id}"
        history = await redis_get(key) or []
        return history[-CHAT_HISTORY_LIMIT:]

    async def append_message(
        self, session_id: str, role: str, content: str
    ) -> None:
        key = f"history:{session_id}"
        history = await redis_get(key) or []
        history.append({"role": role, "content": content})
        # Keep last N messages to control token usage
        history = history[-CHAT_HISTORY_LIMIT:]
        await redis_set(key, history, ttl=self.SESSION_TTL)

    async def clear_session(self, session_id: str) -> None:
        from app.database.redis_client import redis_delete
        await redis_delete(f"history:{session_id}")

    async def build_context(
        self,
        session_id: str,
        user_message: str,
        include_memory: bool = True,
    ) -> tuple[list[dict], str]:
        history = await self.get_history(session_id)
        memory_context = ""
        if include_memory:
            try:
                memory_context = await memory_manager.search_relevant_context(
                    user_message, session_id=session_id
                )
            except Exception as e:
                logger.warning(f"Memory search failed (non-critical): {e}")
        return history, memory_context


context_engine = ContextEngine()
