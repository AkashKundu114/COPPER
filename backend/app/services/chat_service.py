from typing import AsyncGenerator, Optional
from sqlalchemy.orm import Session
from app.ai.orchestration.agent_router import route_message, is_consequential_action
from app.ai.memory.context_engine import context_engine
from app.ai.memory.memory_manager import memory_manager
from app.ai.agents.coding_agent import coding_agent
from app.ai.agents.automation_agent import automation_agent
from app.ai.agents.reminder_agent import reminder_agent
from app.ai.agents.research_agent import research_agent
from app.ai.agents.vision_agent import vision_agent
from app.ai.orchestration.langchain_manager import langchain_manager
from app.ai.llm.prompt_manager import get_system_prompt, build_messages
from app.core.constants import AgentType, LLMProvider
from app.core.guardian import DisagreementLevel
from app.services.guardian_service import guardian_service
from app.core.logger import logger

AGENT_MAP = {
    AgentType.CODING: coding_agent,
    AgentType.AUTOMATION: automation_agent,
    AgentType.REMINDER: reminder_agent,
    AgentType.RESEARCH: research_agent,
    AgentType.VISION: vision_agent,
}


class ChatService:
    async def process_message(
        self,
        session_id: str,
        message: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
        stream: bool = False,
        db: Optional[Session] = None,
    ) -> dict:
        # Route to the right agent
        agent_type = await route_message(message)

        # Guardian pass — only for actions classified as consequential, and
        # only when a db session was supplied (audit logging needs it).
        if db is not None and is_consequential_action(message):
            verdict = await guardian_service.evaluate_action(
                proposed_action=message,
                context=self._build_guardian_context(message, agent_type),
                db=db,
                session_id=session_id,
                actor=str(agent_type),
            )
            if verdict.level >= DisagreementLevel.CHALLENGE:
                from app.core.guardian import guardian_engine
                challenge_text = guardian_engine.format_challenge(verdict)
                return {
                    "response": challenge_text,
                    "agent_type": agent_type,
                    "session_id": session_id,
                    "guardian_verdict": verdict.to_dict(),
                }

        # Get context
        history, memory_context = await context_engine.build_context(session_id, message)

        # Update history with user message
        await context_engine.append_message(session_id, "user", message)

        agent = AGENT_MAP.get(agent_type)
        try:
            if agent:
                response = await agent.run(message, history, memory_context, provider)
            else:
                # Default chat
                system = get_system_prompt(AgentType.CHAT, memory_context)
                messages = build_messages(system, history, message)
                response = await langchain_manager.ainvoke(messages, provider)

            # Save to history and memory
            await context_engine.append_message(session_id, "assistant", response)
            await memory_manager.save_interaction(session_id, message, response, agent_type)

            return {"response": response, "agent_type": agent_type, "session_id": session_id}
        except Exception as e:
            logger.error(f"Chat service error: {e}")
            raise

    async def stream_message(
        self,
        session_id: str,
        message: str,
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> AsyncGenerator[str, None]:
        agent_type = await route_message(message)
        history, memory_context = await context_engine.build_context(session_id, message)
        await context_engine.append_message(session_id, "user", message)

        agent = AGENT_MAP.get(agent_type)
        full_response = []

        try:
            if agent and hasattr(agent, "stream"):
                gen = agent.stream(message, history, memory_context, provider)
            else:
                system = get_system_prompt(AgentType.CHAT, memory_context)
                messages = build_messages(system, history, message)
                gen = langchain_manager.astream(messages, provider)

            async for chunk in gen:
                full_response.append(chunk)
                yield chunk

            complete = "".join(full_response)
            await context_engine.append_message(session_id, "assistant", complete)
            await memory_manager.save_interaction(session_id, message, complete, agent_type)
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"\n[Error: {e}]"

    async def get_history(self, session_id: str) -> list[dict]:
        return await context_engine.get_history(session_id)

    async def clear_history(self, session_id: str) -> None:
        await context_engine.clear_session(session_id)

    def _build_guardian_context(self, message: str, agent_type: AgentType) -> dict:
        """
        Placeholder context builder. Real conflict/commitment detection
        (querying UserMemoryV2 + calendar) lands in a later pass — for now
        this only flags hard-destructive automation/shell actions, so Level 2
        (CHALLENGE) never fires without real evidence behind it.
        """
        msg_lower = message.lower()
        destructive_markers = ["rm -rf", "format ", "del /f", "dd if=", "mkfs", "wipe", "factory reset"]
        return {
            "is_destructive": agent_type == AgentType.AUTOMATION
            and any(m in msg_lower for m in destructive_markers),
        }


chat_service = ChatService()
