import json
from collections.abc import AsyncGenerator
import httpx

from app.ai.llm.model_manager import model_manager
from app.core.config import settings
from app.core.constants import AgentType
from app.core.logger import logger

class OllamaClient:
    def __init__(self):
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = model_manager.get_model("core_agents.chat", "llama3.1:8b")

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                return res.status_code == 200
        except Exception:
            return False

    def select_model(self, agent_type: AgentType | None = None, requested_model: str | None = None) -> str:
        if requested_model:
            return requested_model

        if agent_type == AgentType.CHAT:
            return model_manager.get_model("core_agents.chat", "llama3.1:8b")
        elif agent_type == AgentType.CODING:
            return model_manager.get_model("core_agents.coding", "qwen2.5-coder:7b")
        elif agent_type == AgentType.AUTOMATION:
            return model_manager.get_model("core_agents.automation", "mistral:7b")
        elif agent_type == AgentType.RESEARCH:
            return model_manager.get_model("core_agents.reasoning", "deepseek-r1:7b")
        elif agent_type == AgentType.VISION:
            return model_manager.get_model("vision_agents.vision_primary", "llava:7b")

        return self.default_model

    async def chat(
        self, messages: list[dict[str, str]], agent_type: AgentType | None = None, model: str | None = None
    ) -> str:
        target_model = self.select_model(agent_type, model)
        payload = {"model": target_model, "messages": messages, "stream": False}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content", "")
                else:
                    logger.warning(f"Ollama non-200 ({res.status_code}): {res.text}")
                    return f"Ollama model '{target_model}' is not available (status {res.status_code}). Make sure to run 'ollama pull {target_model}'."
        except Exception as e:
            logger.warning(f"Ollama connection error: {e}")
            return f"Cannot reach the local Ollama LLM server at {self.base_url}. Please launch Ollama on your PC to enable active local reasoning."

    async def stream_chat(
        self, messages: list[dict[str, str]], agent_type: AgentType | None = None, model: str | None = None
    ) -> AsyncGenerator[str, None]:
        target_model = self.select_model(agent_type, model)
        payload = {"model": target_model, "messages": messages, "stream": True}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                    if resp.status_code == 200:
                        async for line in resp.aiter_lines():
                            if line.strip():
                                chunk = json.loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    yield content
                    else:
                        yield f"Ollama returned status {resp.status_code} for '{target_model}'. Run 'ollama pull {target_model}' to download the model into Ollama."
        except Exception as e:
            logger.warning(f"Ollama stream error: {e}")
            yield f"Cannot reach local Ollama server at {self.base_url}. Please start Ollama to chat with C.O.P.P.E.R."

ollama_client = OllamaClient()
