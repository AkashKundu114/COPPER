from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.core.constants import AgentType


class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.AUTOMATION,
            name="FORGE (Automation Agent)",
            description="Autonomous OS automation, command-line execution, file organization, and desktop tool runner.",
            tools=[
                "shell_execute",
                "file_read",
                "file_write",
                "file_list",
                "python_execute",
                "memory_store",
                "memory_query",
            ],
            max_tool_steps=5,
        )

    def get_target_model(self) -> str:
        return model_manager.get_model("core_agents.automation", "mistral:7b")


automation_agent = AutomationAgent()
