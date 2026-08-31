from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.core.constants import AgentType
from app.core.temporal import get_current_temporal_context


class ReminderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.REMINDER,
            name="CHRONOS (Schedule & Reminder Agent)",
            description="Manages daily schedules, calendar events, focus blocks, deadlines, alarms, and reminders with live clock awareness.",
            tools=[
                "calendar_create",
                "reminder_set",
                "memory_query",
                "memory_store",
            ],
            max_tool_steps=5,
        )

    def _build_system_prompt(self, memory_context: str = "") -> str:
        temporal_ctx = get_current_temporal_context()
        combined_ctx = f"{temporal_ctx}\n\n{memory_context}" if memory_context else temporal_ctx
        return super()._build_system_prompt(combined_ctx)

    def get_target_model(self) -> str:
        return model_manager.get_model("core_agents.chat", "llama3.1:8b")


reminder_agent = ReminderAgent()
