from collections.abc import AsyncGenerator
from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.memory.hybrid_search import hybrid_search
from app.ai.memory.reranker import reranker
from app.ai.tools.executor import tool_executor
from app.ai.tools.registry import tool_registry
from app.core.constants import AgentType, LLMProvider
from app.core.logger import logger

CITATION_GROUNDED_RESEARCH_PROMPT_TEMPLATE = """You are OMNI, COPPER's Research Agent with citation grounding.

RETRIEVED SOURCES (ranked by relevance):
{ranked_sources}

RULES:
1. Answer using ONLY the retrieved sources.
2. Cite every claim with [Source N].
3. If sources don't have enough info, say so.
4. Never generate uncited information."""


class ResearchAgent(BaseAgent):
    """
    OMNI (Research Agent) with Hybrid RAG and Citation Grounding.
    Executes hybrid search (vector + BM25) with Reciprocal Rank Fusion,
    applies local cross-encoder re-ranking, and grounds syntheses with [Source N] citations.
    """

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
        return model_manager.get_model("core_agents.reasoning", "deepseek-r1:14b")

    def format_ranked_sources(self, sources: list[dict[str, Any]]) -> str:
        """Formats re-ranked sources into structured citation blocks with relevance scores."""
        if not sources:
            return "No relevant sources found in knowledge base."

        blocks = []
        for idx, s in enumerate(sources, start=1):
            rel = float(s.get("relevance_score", 0.0))
            meta = s.get("metadata") or {}
            source_label = meta.get("filename") or meta.get("source") or s.get("source") or "document"
            content = s.get("content", "").strip()
            blocks.append(
                f"[Source {idx}] (Relevance: {rel:.2f}, Source: {source_label}):\n{content}"
            )
        return "\n\n".join(blocks)

    def _build_citation_system_prompt(self, ranked_sources_text: str) -> str:
        """Builds system prompt integrating citation grounding and available tool specifications."""
        citation_core = CITATION_GROUNDED_RESEARCH_PROMPT_TEMPLATE.format(
            ranked_sources=ranked_sources_text
        )
        if not self.tools:
            return citation_core

        rendered_schemas = tool_registry.render_tool_schemas(self.tools)
        tool_instructions = f"""

AVAILABLE TOOLS:
{rendered_schemas}

HOW TO USE TOOLS:
When retrieved sources lack necessary information and external research is required, you may emit a JSON tool call inside <tool_call> tags:
<tool_call>
{{"tool": "web_search", "arguments": {{"query": "..."}}}}
</tool_call>
When you receive the <tool_result>, incorporate the findings and complete your answer."""

        return f"{citation_core}\n{tool_instructions}"

    async def retrieve_and_rerank(self, query: str, top_k: int = 10, top_n: int = 5) -> list[dict[str, Any]]:
        """Executes Hybrid Search + Cross-Encoder Re-Ranking pipeline."""
        candidates = await hybrid_search.search(query, limit=top_k)
        ranked = await reranker.rerank(query, candidates, top_n=top_n)
        return ranked

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

        # 1. Retrieve via Hybrid Search and Re-Rank
        try:
            top_sources = await self.retrieve_and_rerank(message, top_k=10, top_n=5)
        except Exception as e:
            logger.warning(f"Hybrid retrieval/rerank error in ResearchAgent: {e}")
            top_sources = []

        # 2. Build Citation-Grounded Prompt
        ranked_text = self.format_ranked_sources(top_sources)
        system_prompt = self._build_citation_system_prompt(ranked_text)

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        messages.append({"role": "user", "content": message})
        target_model = self.get_target_model()

        # Tool execution loop
        current_response = ""
        for step in range(self.max_tool_steps):
            try:
                current_response = await ollama_client.chat(
                    messages,
                    model=target_model,
                    agent_type=self.agent_type,
                )
            except Exception as e:
                logger.error(f"LLM chat error in ResearchAgent step {step + 1}: {e}")
                # Fallback to grounded summary
                return (
                    f"Based on retrieved sources:\n\n{ranked_text}\n\n"
                    f"[Notice: Direct inference connection paused, sources surfaced above.]"
                )

            tool_call = tool_executor.parse_tool_call(current_response)
            if not tool_call:
                return current_response

            logger.info(f"ResearchAgent executing tool '{tool_call.tool}' at step {step + 1}")
            result = await tool_executor.execute(
                tool_name=tool_call.tool,
                arguments=tool_call.arguments,
                context={"agent": self.name, "step": step + 1},
            )

            messages.append({"role": "assistant", "content": current_response})
            messages.append({"role": "user", "content": result.format_xml()})

        return current_response

    async def stream(
        self,
        message: str,
        history: list[dict[str, str]] | None = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        if history is None:
            history = []

        try:
            top_sources = await self.retrieve_and_rerank(message, top_k=10, top_n=5)
        except Exception as e:
            logger.warning(f"Hybrid retrieval error in ResearchAgent stream: {e}")
            top_sources = []

        ranked_text = self.format_ranked_sources(top_sources)
        system_prompt = self._build_citation_system_prompt(ranked_text)

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        messages.append({"role": "user", "content": message})
        target_model = self.get_target_model()
        metrics_collector = kwargs.get("metrics_collector")

        for step in range(self.max_tool_steps):
            full_response = []
            async for chunk in ollama_client.stream_chat(
                messages, model=target_model, agent_type=self.agent_type, metrics_collector=metrics_collector
            ):
                full_response.append(chunk)
                yield chunk

            response_text = "".join(full_response)
            tool_call = tool_executor.parse_tool_call(response_text)
            if not tool_call:
                break

            yield f"\n\n🔍 *Research Action:* `{tool_call.tool}`\n"
            result = await tool_executor.execute(
                tool_name=tool_call.tool,
                arguments=tool_call.arguments,
                context={"agent": self.name, "step": step + 1},
            )

            status_icon = "✅" if result.success else "❌"
            yield f"{status_icon} *Observation retrieved.*\n\n"

            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": result.format_xml()})

    async def research(self, query: str, top_n: int = 5) -> dict[str, Any]:
        """
        Direct programmatic research API returning synthesized answer and annotated sources.
        """
        top_sources = await self.retrieve_and_rerank(query, top_k=10, top_n=top_n)
        answer = await self.run(query)
        return {
            "query": query,
            "answer": answer,
            "sources": top_sources,
            "source_count": len(top_sources),
        }


research_agent = ResearchAgent()
