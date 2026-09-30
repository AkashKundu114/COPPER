from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.core.constants import AgentType, LLMProvider
from app.core.guardian import guardian_engine


class GuardianAgent(BaseAgent):
    """
    AEGIS: Constitutional Safety and Security Gatekeeper.
    Performs real-time action reversibility analysis, prompt injection defense, and safety boundary enforcement.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.GUARDIAN,
            name="AEGIS (Safety Guardian)",
            description="Constitutional safety boundary enforcement, action reversibility evaluation, and cognitive fatigue modeling agent.",
            tools=[],
        )

    def get_target_model(self) -> str:
        return model_manager.get_mini_model()

    async def run(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> str:
        context = kwargs.get("guardian_context") or {}
        verdict = guardian_engine.evaluate(message, context)
        return guardian_engine.format_challenge(verdict)


guardian_agent = GuardianAgent()
