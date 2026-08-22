from app.ai.agents.base import BaseAgent
from app.core.constants import AgentType


class ReminderAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.REMINDER,
            name="CHRONOS (Schedule & Reminder Agent)",
            description="Manages daily schedules, focus blocks, deadlines, and reminders.",
        )


reminder_agent = ReminderAgent()
