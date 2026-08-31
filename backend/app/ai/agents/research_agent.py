from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.core.constants import AgentType


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.RESEARCH,
            name="OMNI (Research Agent)",
            description="Deep information retrieval, source comparison, academic reasoning, web searching, and local RAG search agent.",
            tools=[
                "web_search",
                "memory_query",
                "file_read",
                "file_list",
                "memory_store",
            ],
            max_tool_steps=5,
        )

    def get_target_model(self) -> str:
        return model_manager.get_model("core_agents.reasoning", "deepseek-r1:7b")


research_agent = ResearchAgent()
