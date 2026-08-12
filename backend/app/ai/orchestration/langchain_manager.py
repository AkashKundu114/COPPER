from typing import List, Dict, Any, AsyncGenerator
from app.ai.llm.ollama_client import ollama_client
from app.core.constants import LLMProvider
from app.core.logger import logger


class LangchainManager:
    async def ainvoke(self, messages: List[Dict[str, str]], provider: LLMProvider = LLMProvider.OLLAMA) -> str:
        try:
            return await ollama_client.chat(messages)
        except Exception as e:
            logger.warning(f"LangchainManager invocation fallback: {e}")
            last_msg = messages[-1]["content"] if messages else ""
            return f"[COPPER Response]: Processed prompt '{last_msg}'."

    async def astream(self, messages: List[Dict[str, str]], provider: LLMProvider = LLMProvider.OLLAMA) -> AsyncGenerator[str, None]:
        res = await self.ainvoke(messages, provider)
        yield res


langchain_manager = LangchainManager()
