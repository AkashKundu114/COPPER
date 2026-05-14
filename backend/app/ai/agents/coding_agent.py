from typing import AsyncGenerator
from app.ai.llm.prompt_manager import get_system_prompt, build_messages
from app.ai.orchestration.langchain_manager import langchain_manager
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger


class CodingAgent:
    async def run(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> str:
        system = get_system_prompt(AgentType.CODING, context)
        messages = build_messages(system, history, message)
        try:
            return await langchain_manager.ainvoke(messages, provider)
        except Exception as e:
            logger.error(f"CodingAgent error: {e}")
            raise

    async def stream(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> AsyncGenerator[str, None]:
        system = get_system_prompt(AgentType.CODING, context)
        messages = build_messages(system, history, message)
        async for chunk in langchain_manager.astream(messages, provider):
            yield chunk

    async def explain_code(self, code: str, language: str = "python") -> str:
        message = f"Explain this {language} code step by step:\n\n```{language}\n{code}\n```"
        return await self.run(message, [])

    async def fix_bug(self, code: str, error: str, language: str = "python") -> str:
        message = (
            f"Fix this {language} code that produces the error:\n\n"
            f"**Error:** {error}\n\n"
            f"**Code:**\n```{language}\n{code}\n```\n\n"
            "Provide the fixed code with a brief explanation."
        )
        return await self.run(message, [])

    async def review_code(self, code: str, language: str = "python") -> str:
        message = (
            f"Review this {language} code for:\n"
            "- Bugs and potential issues\n"
            "- Performance improvements\n"
            "- Best practices\n"
            "- Security concerns\n\n"
            f"```{language}\n{code}\n```"
        )
        return await self.run(message, [])


coding_agent = CodingAgent()
