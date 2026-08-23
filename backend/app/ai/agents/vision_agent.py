from app.ai.agents.base import BaseAgent
from app.core.constants import AgentType


class VisionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.VISION,
            name="IRIS (Vision Agent)",
            description="Analyzes screenshots, UI layouts, images, and visual content.",
        )


vision_agent = VisionAgent()
