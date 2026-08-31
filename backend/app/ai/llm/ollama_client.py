import json
from collections.abc import AsyncGenerator
from typing import Any

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

    async def get_loaded_models(self) -> list[dict[str, Any]]:
        """
        Queries Ollama /api/ps to inspect models currently loaded in GPU/CPU memory.
        """
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                res = await client.get(f"{self.base_url}/api/ps")
                if res.status_code == 200:
                    return res.json().get("models", [])
                return []
        except Exception as e:
            logger.debug(f"Failed to query loaded models from Ollama: {e}")
            return []

    async def unload_all_models(self) -> str:
        """
        Force Ollama to unload all models from VRAM immediately.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                res = await client.get(f"{self.base_url}/api/ps")
                if res.status_code == 200:
                    loaded = res.json().get("models", [])
                    if not loaded:
                        return "No models were currently loaded in VRAM."

                    unloaded_count = 0
                    for m in loaded:
                        model_name = m.get("name")
                        if model_name:
                            await client.post(f"{self.base_url}/api/chat", json={"model": model_name, "keep_alive": 0})
                            unloaded_count += 1
                    return f"Successfully unloaded {unloaded_count} model(s) from VRAM."
                return f"Failed to get loaded models: HTTP {res.status_code}"
        except Exception as e:
            return f"Error connecting to Ollama to unload models: {e}"

    async def unload_heavy_models(self, keep_mini: bool = True) -> dict[str, Any]:
        """
        Selectively evicts heavy models (7B/8B reasoning, coding, etc.) from GPU VRAM
        while keeping the always-on mini model resident.
        """
        unloaded = []
        kept = []
        try:
            loaded = await self.get_loaded_models()
            async with httpx.AsyncClient(timeout=5.0) as client:
                for m in loaded:
                    m_name = m.get("name", "")
                    if keep_mini and model_manager.is_mini_model(m_name):
                        kept.append(m_name)
                        continue

                    # Unload this model immediately
                    try:
                        await client.post(f"{self.base_url}/api/chat", json={"model": m_name, "keep_alive": 0})
                        unloaded.append(m_name)
                    except Exception as err:
                        logger.warning(f"Could not unload model '{m_name}': {err}")

            return {
                "status": "success",
                "unloaded_models": unloaded,
                "kept_mini_models": kept,
                "total_unloaded": len(unloaded),
            }
        except Exception as e:
            logger.error(f"Error during unload_heavy_models: {e}")
            return {"status": "error", "error": str(e), "unloaded_models": unloaded}

    async def warmup_mini_model(self) -> dict[str, Any]:
        """
        Loads the Always-On Mini Model into VRAM with keep_alive: -1.
        Ensures instantaneous latency for voice interactions and sub-40ms routing.
        """
        mini_tag = model_manager.get_mini_model()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                payload = {
                    "model": mini_tag,
                    "messages": [{"role": "user", "content": "ping"}],
                    "stream": False,
                    "keep_alive": -1,
                }
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    logger.info(f"Warmed up always-on mini model '{mini_tag}' in VRAM (keep_alive: -1)")
                    return {"status": "warmed", "model": mini_tag, "keep_alive": -1}
                else:
                    logger.warning(f"Ollama warmup returned {res.status_code} for '{mini_tag}'")
                    return {"status": "failed", "model": mini_tag, "code": res.status_code}
        except Exception as e:
            logger.debug(f"Mini model warmup skipped (Ollama offline or unavailable): {e}")
            return {"status": "unavailable", "model": mini_tag, "error": str(e)}

    async def keep_only_mini_model_loaded(self) -> dict[str, Any]:
        """
        Enforces system policy: Evicts all heavy models from VRAM and warms up the mini model.
        """
        unload_res = await self.unload_heavy_models(keep_mini=True)
        warmup_res = await self.warmup_mini_model()
        return {
            "vram_policy_enforced": True,
            "unload_result": unload_res,
            "mini_model_warmup": warmup_res,
        }

    def select_model(self, agent_type: AgentType | None = None, requested_model: str | None = None) -> str:
        if requested_model:
            return requested_model

        if agent_type == AgentType.CHAT:
            return model_manager.get_model("core_agents.chat", "llama3.1:8b")
        elif agent_type == AgentType.CODING:
            return model_manager.get_model("core_agents.coding", "qwen2.5-coder:7b")
        elif agent_type == AgentType.DOCUMENT:
            return model_manager.get_document_model()
        elif agent_type == AgentType.AUTOMATION:
            return model_manager.get_model("core_agents.automation", "mistral:7b")
        elif agent_type == AgentType.RESEARCH:
            return model_manager.get_model("core_agents.reasoning", "deepseek-r1:7b")
        elif agent_type == AgentType.VISION:
            return model_manager.get_model("vision_agents.vision_primary", "llava:7b")

        return self.default_model

    async def chat(
        self,
        messages: list[dict[str, str]],
        agent_type: AgentType | None = None,
        model: str | None = None,
        keep_alive: int | str | None = None,
        format: str | dict | None = None,
        metrics_collector: dict | None = None,
    ) -> str:
        target_model = self.select_model(agent_type, model)
        if keep_alive is None:
            keep_alive = model_manager.get_model_keep_alive(target_model)

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "stream": False,
            "keep_alive": keep_alive,
        }
        if format is not None:
            payload["format"] = format

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    if metrics_collector is not None:
                        metrics_collector["model"] = data.get("model", target_model)
                        metrics_collector["prompt_eval_count"] = data.get("prompt_eval_count")
                        metrics_collector["eval_count"] = data.get("eval_count")
                        metrics_collector["eval_duration"] = data.get("eval_duration")
                        metrics_collector["total_duration"] = data.get("total_duration")
                    return data.get("message", {}).get("content", "")
                else:
                    logger.warning(f"Ollama non-200 ({res.status_code}): {res.text}")
                    return f"Ollama model '{target_model}' is not available (status {res.status_code}). Make sure to run 'ollama pull {target_model}'."
        except Exception as e:
            logger.warning(f"Ollama connection error: {e}")
            return f"Cannot reach the local Ollama LLM server at {self.base_url}. Please launch Ollama on your PC to enable active local reasoning."

    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        agent_type: AgentType | None = None,
        model: str | None = None,
        keep_alive: int | str | None = None,
        format: str | dict | None = None,
        metrics_collector: dict | None = None,
    ) -> AsyncGenerator[str, None]:
        target_model = self.select_model(agent_type, model)
        if keep_alive is None:
            keep_alive = model_manager.get_model_keep_alive(target_model)

        payload: dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "stream": True,
            "keep_alive": keep_alive,
        }
        if format is not None:
            payload["format"] = format

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
                                if chunk.get("done") and metrics_collector is not None:
                                    metrics_collector["model"] = chunk.get("model", target_model)
                                    metrics_collector["prompt_eval_count"] = chunk.get("prompt_eval_count")
                                    metrics_collector["eval_count"] = chunk.get("eval_count")
                                    metrics_collector["eval_duration"] = chunk.get("eval_duration")
                                    metrics_collector["total_duration"] = chunk.get("total_duration")
                    else:
                        yield f"Ollama returned status {resp.status_code} for '{target_model}'. Run 'ollama pull {target_model}' to download the model into Ollama."
        except Exception as e:
            logger.warning(f"Ollama stream error: {e}")
            yield f"Cannot reach local Ollama server at {self.base_url}. Please start Ollama to chat with C.O.P.P.E.R."


ollama_client = OllamaClient()
