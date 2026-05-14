from typing import AsyncGenerator
from app.ai.llm.prompt_manager import get_system_prompt, build_messages
from app.ai.orchestration.langchain_manager import langchain_manager
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger


class AutomationAgent:
    async def run(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> str:
        system = get_system_prompt(AgentType.AUTOMATION, context)
        messages = build_messages(system, history, message)
        try:
            return await langchain_manager.ainvoke(messages, provider)
        except Exception as e:
            logger.error(f"AutomationAgent error: {e}")
            raise

    async def stream(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> AsyncGenerator[str, None]:
        system = get_system_prompt(AgentType.AUTOMATION, context)
        messages = build_messages(system, history, message)
        async for chunk in langchain_manager.astream(messages, provider):
            yield chunk

    async def plan_automation(self, task_description: str) -> dict:
        message = (
            f"Create a step-by-step automation plan for this task:\n{task_description}\n\n"
            "Respond in JSON format with keys: steps (list of strings), "
            "estimated_time (string), risks (list of strings), "
            "requires_confirmation (boolean)."
        )
        import json
        response = await self.run(message, [])
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
        except Exception:
            pass
        return {"steps": [response], "estimated_time": "unknown", "risks": [], "requires_confirmation": True}


automation_agent = AutomationAgent()
