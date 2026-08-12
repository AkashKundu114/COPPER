from app.ai.agents.base import BaseAgent
from app.core.constants import AgentType

class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.RESEARCH,
            name="OMNI (Research Agent)",
            description="Handles information retrieval, source comparison, and summarization."
        )

research_agent = ResearchAgent()
