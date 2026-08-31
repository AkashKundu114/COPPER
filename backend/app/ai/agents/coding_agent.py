from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.core.constants import AgentType


class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.CODING,
            name="AXIS (Forge AI Engineer)",
            description="Autonomous coding and software engineering agent capable of writing, analyzing, refactoring, and testing code in a local sandbox or host environment.",
            tools=[
                "python_execute",
                "file_read",
                "file_write",
                "file_list",
                "shell_execute",
                "memory_query",
            ],
            max_tool_steps=5,
        )

    def get_target_model(self) -> str:
        return model_manager.get_model("core_agents.coding", "qwen2.5-coder:7b")


coding_agent = CodingAgent()
