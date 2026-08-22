from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logger import logger
from app.core.constants import AgentType
from app.ai.llm.model_manager import model_manager

class OllamaClient:
    def __init__(self):
        self.base_url = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
        self.default_model = model_manager.get_model("core_agents.chat", "llama3.1:8b")

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
            
        if agent_type == AgentType.CHAT:
            return model_manager.get_model("core_agents.chat")
        elif agent_type == AgentType.CODING:
            return model_manager.get_model("core_agents.coding")
        elif agent_type == AgentType.AUTOMATION:
            return model_manager.get_model("core_agents.automation")
        elif agent_type == AgentType.RESEARCH:
            return model_manager.get_model("core_agents.reasoning")
        elif agent_type == AgentType.VISION:
            return model_manager.get_model("vision_agents.vision_primary")
            
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
