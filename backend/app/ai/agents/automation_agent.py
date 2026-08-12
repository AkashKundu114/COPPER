from app.ai.agents.base import BaseAgent
from app.core.constants import AgentType

class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.AUTOMATION,
            name="FORGE (Automation Agent)",
            description="Executes CLI automation, file organization, and desktop tool runs."
        )

automation_agent = AutomationAgent()
