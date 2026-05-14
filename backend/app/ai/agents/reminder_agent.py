import json
import re
from datetime import datetime
from typing import Optional, AsyncGenerator
from app.ai.llm.prompt_manager import get_system_prompt, build_messages
from app.ai.orchestration.langchain_manager import langchain_manager
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger

EXTRACTION_PROMPT = """Extract reminder details from the user's message.
Return ONLY valid JSON with these keys:
- title: string (short title for the reminder)
- description: string or null
- due_at: ISO 8601 datetime string (infer from context; current time is {now})
- is_recurring: boolean
- recurrence_rule: cron expression string or null (if recurring)

Example output:
{"title": "Team standup", "description": null, "due_at": "2026-05-14T09:00:00", "is_recurring": true, "recurrence_rule": "0 9 * * 1-5"}"""


class ReminderAgent:
    async def extract_reminder(self, message: str) -> Optional[dict]:
        now = datetime.now().isoformat()
        system = EXTRACTION_PROMPT.format(now=now)
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": message},
        ]
        try:
            from app.ai.llm.ollama_client import ollama_client
            response = await ollama_client.chat(messages)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data
        except Exception as e:
            logger.error(f"Reminder extraction error: {e}")
        return None

    async def run(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> str:
        system = get_system_prompt(AgentType.REMINDER, context)
        messages = build_messages(system, history, message)
        try:
            return await langchain_manager.ainvoke(messages, provider)
        except Exception as e:
            logger.error(f"ReminderAgent error: {e}")
            raise

    async def stream(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> AsyncGenerator[str, None]:
        system = get_system_prompt(AgentType.REMINDER, context)
        messages = build_messages(system, history, message)
        async for chunk in langchain_manager.astream(messages, provider):
            yield chunk


reminder_agent = ReminderAgent()
