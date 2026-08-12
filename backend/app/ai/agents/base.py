from typing import List, Dict, Any, AsyncGenerator
from app.core.constants import LLMProvider, AgentType
from app.core.logger import logger

class BaseAgent:

    def __init__(self, agent_type: AgentType, name: str, description: str):
        self.agent_type = agent_type
        self.name = name
        self.description = description

    async def run(self, message: str, history: List[Dict[str, str]], memory_context: str, provider: LLMProvider=LLMProvider.OLLAMA) -> str:
        from app.ai.llm.ollama_client import ollama_client
        prompt = f'System: You are {self.name} agent within C.O.P.P.E.R.\nContext: {memory_context}\nUser: {message}'
        try:
            res = await ollama_client.chat([{'role': 'user', 'content': prompt}])
            return res
        except Exception as e:
            logger.warning(f'Agent {self.name} fallback response: {e}')
            return f"[{self.name} Response]: Processed prompt '{message}'."

    async def stream(self, message: str, history: List[Dict[str, str]], memory_context: str, provider: LLMProvider=LLMProvider.OLLAMA) -> AsyncGenerator[str, None]:
        res = await self.run(message, history, memory_context, provider)
        yield res