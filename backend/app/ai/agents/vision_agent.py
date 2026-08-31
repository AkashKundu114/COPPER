from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.core.constants import AgentType


class VisionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.VISION,
            name="IRIS (Vision Agent)",
            description="Analyzes screenshots, UI layouts, images, and visual content.",
        )

    def get_target_model(self) -> str:
        return model_manager.get_model("vision_agents.vision_primary", "qwen2.5-vl-abliterated:7b")


vision_agent = VisionAgent()
