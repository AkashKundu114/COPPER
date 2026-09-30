from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.orchestration.planner import nexus_planner
from app.core.constants import AgentType, LLMProvider


class PlannerAgent(BaseAgent):
    """
    NEXUS: Strategic Planner and Multi-Agent Task Decomposer.
    Analyzes complex instructions, generates multi-stage DAG task graphs, and orchestrates agent handoffs.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.PLANNER,
            name="NEXUS (Strategic Planner)",
            description="Multi-agent task decomposition, execution graph planning, and DAG orchestration agent.",
            tools=["memory_query", "memory_store"],
            max_tool_steps=5,
        )

    def get_target_model(self) -> str:
        return model_manager.get_model("core_agents.reasoning", "deepseek-r1:14b")

    async def run(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> str:
        plan = await nexus_planner.plan(message, memory_context)
        if plan.tasks:
            task_list = "\n".join(
                f"{i+1}. [{t.agent.upper()}] **{t.title}**: {t.instruction}"
                for i, t in enumerate(plan.tasks)
            )
            return (
                f"📋 **Execution Plan Formulated by NEXUS:**\n"
                f"**Goal**: {plan.goal}\n\n"
                f"**Decomposed Task Sequence:**\n{task_list}"
            )
        return plan.raw_response or f"Plan formulated for: {message}"


planner_agent = PlannerAgent()
