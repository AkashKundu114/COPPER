from app.ai.agents.base import BaseAgent
from app.core.constants import AgentType

class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.CODING,
            name="AXIS (Coding Agent)",
            description="Handles code synthesis, debugging, refactoring, and algorithm analysis."
        )

coding_agent = CodingAgent()
