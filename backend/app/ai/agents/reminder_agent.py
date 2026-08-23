from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger
from app.core.temporal import get_current_temporal_context, save_reminder

SYS_PROMPT = """You are CHRONOS, the Schedule, Alarm, and Task Planner Agent for C.O.P.P.E.R.
You have real-time live clock awareness and schedule precision.
When the user asks to set an alarm, reminder, or schedule a task:
1. Note the EXACT current time provided in your live context.
2. Accurately calculate the remaining time (e.g. from 12:16 AM to 12:20 AM is EXACTLY 4 minutes).
3. Confirm clearly that the alarm / reminder / task has been scheduled.
4. Always state the exact Target Time and Remaining Time accurately.
"""

class ReminderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.REMINDER,
            name="CHRONOS (Schedule & Reminder Agent)",
            description="Manages daily schedules, focus blocks, deadlines, alarms, and reminders with live clock awareness.",
        )

    async def run(
        self,
        message: str,
        history: list = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> str:
        temporal_ctx = get_current_temporal_context()
        combined_ctx = f"{temporal_ctx}\n\n{memory_context}" if memory_context else temporal_ctx

        messages = [
            {"role": "system", "content": f"{SYS_PROMPT}\n\n{combined_ctx}"},
            {"role": "user", "content": message},
        ]

        target_model = model_manager.get_model("core_agents.chat", "llama3.1:8b")
        response = await ollama_client.chat(messages, model=target_model)
        return response

    async def stream(
        self,
        message: str,
        history: list = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ):
        temporal_ctx = get_current_temporal_context()
        combined_ctx = f"{temporal_ctx}\n\n{memory_context}" if memory_context else temporal_ctx

        messages = [
            {"role": "system", "content": f"{SYS_PROMPT}\n\n{combined_ctx}"},
            {"role": "user", "content": message},
        ]

        target_model = model_manager.get_model("core_agents.chat", "llama3.1:8b")
        async for chunk in ollama_client.stream_chat(messages, model=target_model):
            yield chunk

reminder_agent = ReminderAgent()
