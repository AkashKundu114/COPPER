import json
import re
from collections.abc import AsyncGenerator
from typing import Any

from app.ai.agents.base import BaseAgent
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.tools.builtin.web_tools import web_fetch, web_search
from app.core.constants import AgentType, LLMProvider
from app.core.data_firewall import redact
from app.core.logger import logger

RAPTOR_SYSTEM_PROMPT = """You are RAPTOR, COPPER's Web Search Agent. You bridge offline-first architecture with the open web — ONLY when needed.

To search:
<search>{"query": "your query", "num_results": 5}</search>

To fetch a page:
<fetch>{"url": "https://...", "extract": "text"}</fetch>

RULES:
1. Start with search. Never guess URLs.
2. Fetch at most 3 pages per query.
3. Synthesize from multiple sources.
4. Cite with [Source: URL].
5. PRIVACY: Never send user PII or COPPER memory content in search queries.
6. All web access is logged in audit trail."""


class WebSearchAgent(BaseAgent):
    """
    RAPTOR: Privacy-preserving Local Web Search Agent.
    Bridges COPPER's offline-first architecture with the open web via a local SearXNG metasearch instance.
    Runs a ReAct loop with <search> and <fetch> tags, strictly enforcing a 3-page fetch limit,
    data firewall PII stripping, and [Source: URL] citation grounding.
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.WEB_SEARCH,
            name="RAPTOR (Web Search Agent)",
            description="Local privacy-preserving web search agent via SearXNG and clean-text page extraction.",
            tools=["web_search", "web_fetch"],
            max_tool_steps=6,
        )
        self.max_fetches_per_turn = 3

    def get_target_model(self) -> str:
        return model_manager.get_model("core_agents.web_search", "mistral:7b")

    def _build_system_prompt(self, memory_context: str = "") -> str:
        # Internal memory content is kept private and not passed to web search prompts
        return RAPTOR_SYSTEM_PROMPT

    def _parse_action(self, text: str) -> tuple[str | None, dict[str, Any] | None, str]:
        """
        Parses <search>...</search> or <fetch>...</fetch> tags from model output.
        Falls back to standard <tool_call> if emitted.
        Returns (action_type, payload_dict, matched_tag_str).
        """
        # 1. Check <search> tag
        search_match = re.search(r"<search>(.*?)</search>", text, re.DOTALL | re.IGNORECASE)
        if search_match:
            raw = search_match.group(1).strip()
            payload = self._parse_json_or_raw(raw, default_key="query")
            return "search", payload, search_match.group(0)

        # 2. Check <fetch> tag
        fetch_match = re.search(r"<fetch>(.*?)</fetch>", text, re.DOTALL | re.IGNORECASE)
        if fetch_match:
            raw = fetch_match.group(1).strip()
            payload = self._parse_json_or_raw(raw, default_key="url")
            return "fetch", payload, fetch_match.group(0)

        # 3. Fallback: <tool_call> tag
        tool_match = re.search(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL | re.IGNORECASE)
        if tool_match:
            try:
                data = json.loads(tool_match.group(1).strip())
                tool_name = data.get("tool")
                args = data.get("arguments", {})
                if tool_name == "web_search":
                    return "search", args, tool_match.group(0)
                elif tool_name == "web_fetch":
                    return "fetch", args, tool_match.group(0)
            except Exception:
                pass

        return None, None, ""

    def _parse_json_or_raw(self, raw: str, default_key: str) -> dict[str, Any]:
        """Attempts JSON parse; falls back to treating raw string as default key value."""
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        code_match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", raw)
        if code_match:
            try:
                parsed = json.loads(code_match.group(1))
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

        return {default_key: raw}

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

        system_prompt = self._build_system_prompt()
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        messages.append({"role": "user", "content": message})
        target_model = self.get_target_model()

        fetch_count = 0
        current_response = ""

        for step in range(self.max_tool_steps):
            try:
                current_response = await ollama_client.chat(
                    messages,
                    model=target_model,
                    agent_type=self.agent_type,
                )
            except Exception as e:
                logger.error(f"LLM chat error in RAPTOR step {step + 1}: {e}")
                return f"[RAPTOR Error]: Could not complete reasoning: {e}"

            action_type, payload, tag_str = self._parse_action(current_response)
            if not action_type:
                # No further web actions requested; return synthesized response
                return current_response

            observation_content = ""

            if action_type == "search":
                query = payload.get("query", "")
                num_results = int(payload.get("num_results", 5))
                # Privacy: strip PII and any memory leakage
                sanitized_query = redact(query).strip()
                logger.info(f"RAPTOR executing web search for: '{sanitized_query}'")
                search_res = await web_search(query=sanitized_query, num_results=num_results)
                observation_content = json.dumps(search_res, indent=2)

            elif action_type == "fetch":
                url = payload.get("url", "").strip()
                if fetch_count >= self.max_fetches_per_turn:
                    observation_content = (
                        f"Error: Maximum {self.max_fetches_per_turn} page fetches reached for this query. "
                        f"Synthesize your answer now using the sources already gathered."
                    )
                    logger.warning("RAPTOR reached maximum 3 page fetches per turn limit")
                else:
                    fetch_count += 1
                    logger.info(f"RAPTOR fetching page ({fetch_count}/{self.max_fetches_per_turn}): '{url}'")
                    fetch_res = await web_fetch(url=url, extract=payload.get("extract", "text"))
                    observation_content = json.dumps(fetch_res, indent=2)

            messages.append({"role": "assistant", "content": current_response})
            messages.append({"role": "user", "content": f"<observation>\n{observation_content}\n</observation>"})

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

        system_prompt = self._build_system_prompt()
        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for h in history[-6:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})

        messages.append({"role": "user", "content": message})
        target_model = self.get_target_model()
        metrics_collector = kwargs.get("metrics_collector")

        fetch_count = 0

        for step in range(self.max_tool_steps):
            full_response = []
            async for chunk in ollama_client.stream_chat(
                messages, model=target_model, agent_type=self.agent_type, metrics_collector=metrics_collector
            ):
                full_response.append(chunk)
                yield chunk

            response_text = "".join(full_response)
            action_type, payload, tag_str = self._parse_action(response_text)
            if not action_type:
                break

            observation_content = ""

            if action_type == "search":
                query = payload.get("query", "")
                num_results = int(payload.get("num_results", 5))
                sanitized_query = redact(query).strip()
                yield f"\n\n🔍 *RAPTOR searching:* `{sanitized_query}`...\n"

                search_res = await web_search(query=sanitized_query, num_results=num_results)
                observation_content = json.dumps(search_res, indent=2)
                yield f"\n📋 *Found {search_res.get('count', 0)} sources.*\n\n"

            elif action_type == "fetch":
                url = payload.get("url", "").strip()
                if fetch_count >= self.max_fetches_per_turn:
                    observation_content = (
                        f"Error: Maximum {self.max_fetches_per_turn} page fetches reached for this query. "
                        f"Synthesize your answer now using the sources already gathered."
                    )
                    yield f"\n\n⚠️ *Max fetch limit reached ({self.max_fetches_per_turn} pages). Synthesizing...*\n\n"
                else:
                    fetch_count += 1
                    yield f"\n\n🌐 *RAPTOR fetching ({fetch_count}/{self.max_fetches_per_turn}):* `{url}`...\n"
                    fetch_res = await web_fetch(url=url, extract=payload.get("extract", "text"))
                    observation_content = json.dumps(fetch_res, indent=2)
                    yield f"\n📄 *Page content extracted ({fetch_res.get('length', 0)} chars).*\n\n"

            messages.append({"role": "assistant", "content": response_text})
            messages.append({"role": "user", "content": f"<observation>\n{observation_content}\n</observation>"})


web_search_agent = WebSearchAgent()
raptor_agent = web_search_agent
