from collections.abc import AsyncGenerator

from app.ai.llm.ollama_client import ollama_client
from app.core.config import settings
from app.core.constants import LLMProvider
from app.core.logger import logger


class LangchainManager:
    async def ainvoke(
        self,
        messages: list[dict[str, str]],
        provider: LLMProvider = LLMProvider.OLLAMA,
        model: str | None = None,
        metrics_collector: dict | None = None,
    ) -> str:
        if settings.COPPER_DEMO:
            user_msg = messages[-1].get("content", "") if messages else ""
            return f"[DEMO MODE] COPPER Assistant received: '{user_msg}'. Operating in offline demo mode."
        try:
            return await ollama_client.chat(messages, model=model, metrics_collector=metrics_collector)
        except Exception as e:
            logger.warning(f"LangchainManager invocation fallback: {e}")
            if settings.COPPER_DEMO:
                return "[DEMO MODE] Ollama unavailable. Operating in offline demo mode."
            return "Cannot reach local LLM server. Please ensure Ollama is running."

    async def astream(
        self,
        messages: list[dict[str, str]],
        provider: LLMProvider = LLMProvider.OLLAMA,
        model: str | None = None,
        metrics_collector: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        if settings.COPPER_DEMO:
            user_msg = messages[-1].get("content", "") if messages else ""
            for word in f"[DEMO MODE] COPPER Assistant response to '{user_msg}'.".split(" "):
                yield word + " "
            return
        try:
            async for chunk in ollama_client.stream_chat(messages, model=model, metrics_collector=metrics_collector):
                yield chunk
        except Exception as e:
            logger.warning(f"LangchainManager stream fallback: {e}")
            if settings.COPPER_DEMO:
                yield "[DEMO MODE] Ollama unavailable. Operating in offline demo mode."
                return
            yield "Cannot reach local LLM server. Please ensure Ollama is running."


langchain_manager = LangchainManager()
