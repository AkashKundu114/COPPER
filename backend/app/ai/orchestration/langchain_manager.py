from typing import Optional, AsyncGenerator
from langchain_community.chat_models import ChatOllama
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from app.core.config import settings
from app.core.constants import LLMProvider
from app.core.logger import logger


class LangChainManager:
    def __init__(self):
        self._ollama: Optional[ChatOllama] = None
        self._openai: Optional[ChatOpenAI] = None

    def get_ollama(self) -> ChatOllama:
        if self._ollama is None:
            self._ollama = ChatOllama(
                model=settings.OLLAMA_MODEL,
                base_url=settings.OLLAMA_HOST,
                temperature=0.7,
            )
        return self._ollama

    def get_openai(self) -> ChatOpenAI:
        if self._openai is None:
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY not set")
            self._openai = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                api_key=settings.OPENAI_API_KEY,
                temperature=0.7,
                streaming=True,
            )
        return self._openai

    def get_llm(self, provider: LLMProvider = LLMProvider.OLLAMA):
        if provider == LLMProvider.OPENAI:
            return self.get_openai()
        return self.get_ollama()

    def build_langchain_messages(self, messages: list[dict]):
        result = []
        for m in messages:
            role = m["role"]
            content = m["content"]
            if role == "system":
                result.append(SystemMessage(content=content))
            elif role == "user":
                result.append(HumanMessage(content=content))
            elif role == "assistant":
                result.append(AIMessage(content=content))
        return result

    async def astream(
        self,
        messages: list[dict],
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> AsyncGenerator[str, None]:
        llm = self.get_llm(provider)
        lc_messages = self.build_langchain_messages(messages)
        try:
            async for chunk in llm.astream(lc_messages):
                if hasattr(chunk, "content") and chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error(f"LangChain stream error: {e}")
            raise

    async def ainvoke(
        self,
        messages: list[dict],
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> str:
        llm = self.get_llm(provider)
        lc_messages = self.build_langchain_messages(messages)
        try:
            result = await llm.ainvoke(lc_messages)
            return result.content
        except Exception as e:
            logger.error(f"LangChain invoke error: {e}")
            raise


langchain_manager = LangChainManager()
