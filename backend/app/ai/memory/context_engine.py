from typing import Tuple, List, Dict, Any
from app.ai.memory.memory_manager import memory_manager
from app.core.logger import logger
_session_history: Dict[str, List[Dict[str, str]]] = {}

class ContextEngine:

    async def build_context(self, session_id: str, message: str) -> Tuple[List[Dict[str, str]], str]:
        history = _session_history.get(session_id, [])
        try:
            epistemic_memories = await memory_manager.get_relevant_memories(message)
            memory_text = '\n'.join([f"- [{m.get('memory_type', 'fact').upper()}] {m.get('content')}" for m in epistemic_memories])
        except Exception as e:
            logger.warning(f'Memory context retrieval fallback: {e}')
            memory_text = ''
        return (history, memory_text)

    async def append_message(self, session_id: str, role: str, content: str):
        if session_id not in _session_history:
            _session_history[session_id] = []
        _session_history[session_id].append({'role': role, 'content': content})

    async def get_history(self, session_id: str) -> List[Dict[str, str]]:
        return _session_history.get(session_id, [])

    async def clear_session(self, session_id: str):
        _session_history.pop(session_id, None)
context_engine = ContextEngine()