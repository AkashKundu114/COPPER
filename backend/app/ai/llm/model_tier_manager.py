"""
Tiered inference / VRAM discipline manager.

Policy:
- Exactly one "Gatekeeper" model is pinned in VRAM permanently (keep_alive=-1).
  It handles wake-word confirmation, fast-path routing fallback, and trivial
  turns, so the GPU never has to cold-load a 7B model just to say "hi".
- Every other model ("heavy" tier: chat/coding/automation/reasoning/vision/
  document drafting) is loaded on demand with a numeric keep_alive window and
  actively unloaded by a background sweep once that window has elapsed.
- Unloading reuses the same Ollama trick already used by
  `OllamaClient.unload_all_models()`: POST /api/chat with keep_alive=0.

This module wraps `ollama_client` rather than replacing it — call
`model_tier_manager.chat(...)` instead of `ollama_client.chat(...)` from agents
that care about tiering; agents that don't care can keep calling
`ollama_client.chat(...)` directly and simply won't participate in the idle
sweep (they'll behave exactly as before this patch).
"""

import asyncio
import time
from dataclasses import dataclass, field

import httpx

from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.core.config import settings
from app.core.logger import logger

GATEKEEPER_MODEL_PATH = "gatekeeper.mini"


@dataclass
class _LoadedModelState:
    model_name: str
    last_used_at: float = field(default_factory=time.time)
    idle_timeout_seconds: int = 240


class ModelTierManager:
    def __init__(self):
        self.gatekeeper_model = model_manager.get_model(GATEKEEPER_MODEL_PATH, default="qwen2.5:0.5b-instruct-q4_K_M")
        self._resident: dict[str, _LoadedModelState] = {}
        self._sweep_task: asyncio.Task | None = None
        self._base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")

    # ------------------------------------------------------------------ #
    # Public chat entry points
    # ------------------------------------------------------------------ #
    async def chat_gatekeeper(self, messages: list[dict[str, str]]) -> str:
        """Always issued with keep_alive=-1. This model is never swept."""
        return await self._chat_with_keep_alive(self.gatekeeper_model, messages, keep_alive=-1)

    async def chat_heavy(self, model: str, messages: list[dict[str, str]], idle_timeout_seconds: int = 240) -> str:
        """Issued with a numeric keep_alive window; tracked for the idle sweep."""
        self._touch(model, idle_timeout_seconds)
        return await self._chat_with_keep_alive(model, messages, keep_alive=f"{idle_timeout_seconds}s")

    async def _chat_with_keep_alive(self, model: str, messages: list[dict[str, str]], keep_alive) -> str:
        payload = {"model": model, "messages": messages, "stream": False, "keep_alive": keep_alive}
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self._base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    return res.json().get("message", {}).get("content", "")
                logger.warning(f"[tier-manager] Ollama non-200 for {model}: {res.status_code}")
                return await ollama_client.chat(messages, model=model)
        except Exception as e:
            logger.warning(f"[tier-manager] chat error for {model}: {e}")
            return await ollama_client.chat(messages, model=model)

    # ------------------------------------------------------------------ #
    # Idle sweep — unloads heavy models, never touches the Gatekeeper
    # ------------------------------------------------------------------ #
    def _touch(self, model: str, idle_timeout_seconds: int) -> None:
        if model == self.gatekeeper_model:
            return
        self._resident[model] = _LoadedModelState(model_name=model, idle_timeout_seconds=idle_timeout_seconds)

    async def _unload(self, model: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(f"{self._base_url}/api/chat", json={"model": model, "keep_alive": 0})
            logger.info(f"[tier-manager] Unloaded idle heavy model: {model}")
        except Exception as e:
            logger.warning(f"[tier-manager] Failed to unload {model}: {e}")

    async def _sweep_loop(self) -> None:
        while True:
            await asyncio.sleep(15)
            now = time.time()
            expired = [
                m for m, st in self._resident.items() if (now - st.last_used_at) >= st.idle_timeout_seconds
            ]
            for model in expired:
                await self._unload(model)
                self._resident.pop(model, None)

    def start(self) -> None:
        if self._sweep_task is None:
            self._sweep_task = asyncio.ensure_future(self._sweep_loop())
            logger.info(
                f"[tier-manager] Started. Gatekeeper pinned: {self.gatekeeper_model} "
                f"(keep_alive=-1). Heavy-tier idle sweep every 15s."
            )

    def stop(self) -> None:
        if self._sweep_task:
            self._sweep_task.cancel()
            self._sweep_task = None

    def status(self) -> dict:
        return {
            "gatekeeper_model": self.gatekeeper_model,
            "gatekeeper_pinned": True,
            "heavy_models_resident": [
                {"model": m, "idle_seconds": round(time.time() - st.last_used_at, 1)}
                for m, st in self._resident.items()
            ],
        }


model_tier_manager = ModelTierManager()
