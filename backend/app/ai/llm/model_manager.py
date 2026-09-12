import json
from pathlib import Path
from typing import Any

from app.core.logger import logger

MANIFEST_PATH = Path(__file__).parent.parent.parent.parent.parent / "ai-models" / "models_manifest.json"

MINI_MODEL_IDENTIFIERS = {
    "llama-3.2-1b-instruct",
    "llama-3.2-1b-instruct-abliterated",
    "llama3.2:1b",
    "llama3.2-abliterated:1b",
    "llama3.2:3b",
    "llama-3.2-3b-instruct-abliterated",
    "qwen2.5-0.5b-instruct",
    "qwen2.5-0.5b-instruct-abliterated",
    "qwen2.5:0.5b",
    "qwen2.5-abliterated:0.5b",
    "qwen2.5-coder-0.5b-instruct",
    "qwen2.5-coder-0.5b-instruct-abliterated",
    "qwen2.5-coder:0.5b",
    "qwen2.5-coder-abliterated:0.5b",
    "smollm2-360m-instruct",
    "smollm2-360m-instruct-abliterated",
    "smollm2:360m",
    "smollm2-abliterated:360m",
    "smollm2-1.7b-instruct",
    "smollm2-1.7b-instruct-abliterated",
    "smollm2:1.7b",
    "smollm2-abliterated:1.7b",
    "qwen2.5-1.5b-instruct",
    "qwen2.5-1.5b-instruct-abliterated",
    "qwen2.5:1.5b",
    "qwen2.5-abliterated:1.5b",
    "qwen2.5-coder:3b",
    "qwen2.5-coder-3b-instruct",
    "qwen2.5-vl:3b",
    "deepseek-r1:1.5b",
    "deepseek-r1-distill-qwen-1.5b",
    "granite-3.2-2b-instruct",
    "granite-guardian-3.1-2b",
    "moondream",
}


class ModelManager:
    def __init__(self):
        self.manifest: dict[str, Any] = {}
        self.load_manifest()

    def load_manifest(self):
        try:
            if MANIFEST_PATH.exists():
                with open(MANIFEST_PATH, encoding="utf-8") as f:
                    self.manifest = json.load(f)
                logger.info(f"Loaded models manifest from {MANIFEST_PATH}")
            else:
                logger.warning(f"Models manifest not found at {MANIFEST_PATH}")
        except Exception as e:
            logger.error(f"Failed to load models manifest: {e}")

    def get_model(self, path: str, default: str = "qwen2.5:14b") -> str:
        """
        Retrieves the Ollama tag from the manifest using dot notation (falling back to name or default).
        Example: get_model("core_agents.chat") -> "qwen2.5:14b"
        """
        try:
            parts = path.split(".")
            current = self.manifest
            for part in parts:
                current = current.get(part, {})

            if isinstance(current, dict):
                return current.get("ollama_tag") or current.get("name", default)

            logger.warning(f"Model path '{path}' not found in manifest. Using default: {default}")
            return default

        except Exception as e:
            logger.error(f"Error resolving model path '{path}': {e}")
            return default

    def get_ollama_tag(self, path: str, default: str = "qwen2.5:14b") -> str:
        """
        Retrieves the Ollama tag from the manifest using dot notation.
        Example: get_ollama_tag("core_agents.chat") -> "qwen2.5:14b"
        """
        try:
            parts = path.split(".")
            current = self.manifest
            for part in parts:
                current = current.get(part, {})

            if isinstance(current, dict):
                return current.get("ollama_tag") or current.get("name", default)

            return default
        except Exception as e:
            logger.error(f"Error resolving Ollama tag for '{path}': {e}")
            return default

    def get_mini_model(self, prefer_tag: bool = True) -> str:
        """
        Returns the configured Always-On Mini Model name or Ollama tag.
        This model is kept loaded in VRAM with keep_alive: -1 for fast voice and sub-40ms routing.
        """
        mini_cfg = self.manifest.get("always_on_mini_model", {})
        if prefer_tag and mini_cfg.get("ollama_tag"):
            return mini_cfg["ollama_tag"]
        return mini_cfg.get("name", "llama3.2:1b")

    def get_document_model(self, prefer_tag: bool = True) -> str:
        """
        Returns the primary document generation model.
        """
        doc_cfg = self.manifest.get("core_agents", {}).get("document", {})
        if prefer_tag and doc_cfg.get("ollama_tag"):
            return doc_cfg["ollama_tag"]
        return doc_cfg.get("name", "phi4:14b")

    def is_mini_model(self, model_name: str | None) -> bool:
        """
        Determines whether a model name or tag qualifies as an always-on mini model.
        """
        if not model_name:
            return False
        clean = model_name.strip().lower()
        if clean in MINI_MODEL_IDENTIFIERS:
            return True
        # Check against manifest always_on_mini_model
        mini_cfg = self.manifest.get("always_on_mini_model", {})
        if clean == mini_cfg.get("name", "").lower() or clean == mini_cfg.get("ollama_tag", "").lower():
            return True
        return any(
            clean.startswith(prefix) for prefix in ["llama3.2:1b", "qwen2.5:0.5b", "smollm2:", "qwen2.5-coder:0.5b"]
        )

    def get_model_keep_alive(self, model_name: str | None) -> int | str:
        """
        Returns the keep-alive policy:
        - Mini model: -1 (infinite residency in VRAM for instant voice turns and routing)
        - Heavy models (7B/8B): '2m' or short duration to minimize GPU strain
        """
        if self.is_mini_model(model_name):
            return -1
        policy = self.manifest.get("vram_policy", {})
        return policy.get("heavy_model_keep_alive", "2m")

    def get_vram_policy(self) -> dict[str, Any]:
        return self.manifest.get(
            "vram_policy",
            {
                "always_on_mini_model": "llama3.2:1b",
                "mini_model_keep_alive": -1,
                "heavy_model_keep_alive": "2m",
                "auto_unload_heavy_after_turn": True,
                "target_idle_vram_gb": 1.0,
            },
        )

    def resolve_model_alias(self, alias: str) -> tuple[str, str]:
        """
        Resolves a user-friendly alias, size, or model family to an Ollama model tag and readable tier name.
        Returns: (ollama_tag, tier_display_name)
        """
        clean = alias.strip().lower()
        if any(w in clean for w in ["mini", "small", "smaller", "tiny", "1b", "lightweight", "fast", "instant"]):
            tag = self.get_mini_model(prefer_tag=True)
        if any(w in clean for w in ["3b", "coder-micro", "shell"]):
            return "qwen2.5-coder:3b", "FORGE / WARDEN (~3B Code & Shell Tier)"
        if any(w in clean for w in ["0.5b", "1.5b", "reflex", "gatekeeper", "firewall", "router"]):
            return "qwen2.5:1.5b", "MERCURY / AEGIS (1.5B Reflex Tier)"
        if any(w in clean for w in ["14b", "large", "full", "heavy", "atlas", "standard", "default"]):
            tag = self.get_model("core_agents.chat", "qwen2.5:14b")
            return tag, "ATLAS (14B Standard Cognitive Tier)"
        if "deepseek" in clean or "reason" in clean or "math" in clean:
            if "1.5" in clean:
                return "deepseek-r1:1.5b", "CRUCIBLE Reasoning (~1.5B Tier)"
            tag = self.get_model("core_agents.reasoning", "deepseek-r1:14b")
            return tag, "PROMETHEUS DeepSeek Reasoning (14B Tier)"
        if "coder" in clean or "code" in clean:
            return self.get_model("core_agents.coding", "qwen2.5-coder-abliterated:14b"), "VULCAN Coder (14B Tier)"
        if "phi" in clean or "document" in clean or "report" in clean:
            return self.get_model("core_agents.document", "phi4:14b"), "SCRIBE Document Synthesis (14B Tier)"
        if "mistral" in clean or "automation" in clean or "tool" in clean:
            return self.get_model("core_agents.automation", "mistral-nemo:12b"), "DAEMON Task Automation (12B Tier)"

        return self.get_model("core_agents.chat", "qwen2.5:14b"), "ATLAS Default Chat (14B Tier)"


model_manager = ModelManager()
