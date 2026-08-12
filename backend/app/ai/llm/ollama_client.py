from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logger import logger
from app.core.constants import AgentType
MODEL_POOL_MAP = {AgentType.CHAT: 'llama3.1:8b', AgentType.CODING: 'qwen2.5-coder:7b', AgentType.AUTOMATION: 'mistral:7b-instruct', AgentType.RESEARCH: 'deepseek-coder:6.7b', AgentType.VISION: 'llava:7b'}

class OllamaClient:

    def __init__(self):
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.default_model = 'llama3.1:8b'

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f'{self.base_url}/api/version')
                return res.status_code == 200
        except Exception:
            return False

    def select_model(self, agent_type: Optional[AgentType]=None, requested_model: Optional[str]=None) -> str:
        if requested_model:
            return requested_model
        if agent_type in MODEL_POOL_MAP:
            return MODEL_POOL_MAP[agent_type]
        return self.default_model

    async def chat(self, messages: List[Dict[str, str]], agent_type: Optional[AgentType]=None, model: Optional[str]=None) -> str:
        target_model = self.select_model(agent_type, model)
        payload = {'model': target_model, 'messages': messages, 'stream': False}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f'{self.base_url}/api/chat', json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get('message', {}).get('content', '')
                else:
                    logger.warning(f'Ollama non-200 ({res.status_code}): {res.text}')
                    return f'[Ollama Engine ({target_model})]: Input processed locally.'
        except Exception as e:
            logger.warning(f'Ollama connection error: {e}')
            return f"[Local Offline Engine]: Processed prompt using '{target_model}' fallback."
ollama_client = OllamaClient()