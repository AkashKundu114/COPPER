from app.ai.memory.memory_manager import memory_manager
from app.ai.memory.persistent_memory import persistent_memory
from app.core.logger import logger
from app.core.temporal import get_current_temporal_context
from app.services.self_model_service import self_model_service


class ContextEngine:
    async def build_context(self, session_id: str, message: str) -> tuple[list[dict[str, str]], str, str]:
        history = persistent_memory.get_history(session_id)
        temporal_snippet = get_current_temporal_context()
        profile_snippet = persistent_memory.get_memory_prompt_snippet()

        epistemic_parts = [temporal_snippet, profile_snippet]
        try:
            epistemic_memories = await memory_manager.get_relevant_memories(message)
            if epistemic_memories:
                epistemic_parts.append(
                    "\n• Dynamically Retrieved Context:\n"
                    + "\n".join(
                        [f"- [{m.get('memory_type', 'fact').upper()}] {m.get('content')}" for m in epistemic_memories]
                    )
                )
        except Exception as e:
            logger.warning(f"Memory context retrieval fallback: {e}")

        memory_text = "\n\n".join(epistemic_parts)
        self_context = await self_model_service.build_self_context(message)

        return (history, memory_text, self_context)

    async def append_message(self, session_id: str, role: str, content: str):
        if role == "user":
            if self_model_service.detect_correction(content):
                history = persistent_memory.get_history(session_id)
                last_assistant_msg = ""
                for msg in reversed(history):
                    if msg.get("role") == "assistant":
                        last_assistant_msg = msg.get("content", "")
                        break
                await self_model_service.record_correction(content, last_assistant_msg, session_id)

        persistent_memory.append_message(session_id, role, content)
        if role == "user":
            persistent_memory.extract_and_store_facts(content)

    async def get_history(self, session_id: str) -> list[dict[str, str]]:
        return persistent_memory.get_history(session_id)

    async def clear_session(self, session_id: str):
        if session_id in persistent_memory.sessions:
            persistent_memory.sessions.pop(session_id, None)
            persistent_memory._save_sessions()


context_engine = ContextEngine()
