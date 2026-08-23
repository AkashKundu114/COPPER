from collections.abc import AsyncGenerator

from app.ai.llm.ollama_client import ollama_client
from app.core.constants import LLMProvider
from app.core.logger import logger

class LangchainManager:
    async def ainvoke(self, messages: list[dict[str, str]], provider: LLMProvider = LLMProvider.OLLAMA) -> str:
        try:
            return await ollama_client.chat(messages)
        except Exception as e:
            logger.warning(f"LangchainManager invocation fallback: {e}")
            return f"Cannot reach local LLM server. Please ensure Ollama is running."

    async def astream(
        self, messages: list[dict[str, str]], provider: LLMProvider = LLMProvider.OLLAMA
    ) -> AsyncGenerator[str, None]:
        try:
            async for chunk in ollama_client.stream_chat(messages):
                yield chunk
        except Exception as e:
            logger.warning(f"LangchainManager stream fallback: {e}")
            yield f"Cannot reach local LLM server. Please ensure Ollama is running."

langchain_manager = LangchainManager()
