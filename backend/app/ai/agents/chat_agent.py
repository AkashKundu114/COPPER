from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.prompt_manager import build_messages, get_system_prompt
from app.ai.orchestration.langchain_manager import langchain_manager
from app.core.constants import AgentType, LLMProvider


class ChatAgent(BaseAgent):
    """
    ATLAS: Primary conversational interface and dialogue orchestrator.
    Handles general knowledge, conversational flow, persona alignment, and multi-turn dialogue.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.CHAT,
            name="ATLAS (Conversational Interface)",
            description="Primary conversational companion, dialogue orchestrator, and high-level reasoning agent.",
            tools=[],
        )

    def get_target_model(self) -> str:
        return model_manager.get_model("core_agents.chat", "qwen2.5:14b")

    async def run(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> str:
        if history is None:
            history = []
        target_model = self.get_target_model()
        self_context = kwargs.get("self_context", "")
        system = get_system_prompt(AgentType.CHAT, memory_context, self_context, model_name=target_model)
        messages = build_messages(system, history, message)
        return await langchain_manager.ainvoke(messages, provider, model=target_model)


chat_agent = ChatAgent()
