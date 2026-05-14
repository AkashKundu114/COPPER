from typing import AsyncGenerator
from app.ai.llm.prompt_manager import get_system_prompt, build_messages
from app.ai.orchestration.langchain_manager import langchain_manager
from app.ai.memory.memory_manager import memory_manager
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger


class ResearchAgent:
    async def run(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> str:
        # Search documents for extra context
        doc_results = await memory_manager.search_documents(message, limit=3)
        doc_context = "\n\n".join(
            [f"[Source: {r['metadata'].get('source', 'unknown')}]\n{r['document']}"
             for r in doc_results]
        )
        full_context = "\n\n".join(filter(None, [context, doc_context]))
        system = get_system_prompt(AgentType.RESEARCH, full_context)
        messages = build_messages(system, history, message)
        try:
            return await langchain_manager.ainvoke(messages, provider)
        except Exception as e:
            logger.error(f"ResearchAgent error: {e}")
            raise

    async def stream(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> AsyncGenerator[str, None]:
        doc_results = await memory_manager.search_documents(message, limit=3)
        doc_context = "\n\n".join(
            [r["document"] for r in doc_results]
        )
        full_context = "\n\n".join(filter(None, [context, doc_context]))
        system = get_system_prompt(AgentType.RESEARCH, full_context)
        messages = build_messages(system, history, message)
        async for chunk in langchain_manager.astream(messages, provider):
            yield chunk

    async def summarize(self, text: str, format: str = "bullet") -> str:
        formats = {
            "bullet": "Summarize in bullet points with key takeaways.",
            "paragraph": "Summarize in 2-3 concise paragraphs.",
            "tldr": "Give a 1-2 sentence TL;DR summary.",
        }
        instruction = formats.get(format, formats["bullet"])
        message = f"{instruction}\n\nText to summarize:\n{text}"
        return await self.run(message, [])

    async def compare(self, items: list[str], criteria: list[str] = None) -> str:
        criteria_str = ", ".join(criteria) if criteria else "features, pros/cons, use cases"
        items_str = " vs ".join(items)
        message = f"Compare {items_str} based on: {criteria_str}. Use a clear structured format."
        return await self.run(message, [])


research_agent = ResearchAgent()
