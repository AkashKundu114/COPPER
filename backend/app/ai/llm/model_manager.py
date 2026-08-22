import json
from pathlib import Path
from typing import Optional
from app.core.logger import logger

MANIFEST_PATH = Path(__file__).parent.parent.parent.parent.parent / "ai-models" / "models_manifest.json"

class ModelManager:
    def __init__(self):
        self.manifest = {}
        self.load_manifest()

    def load_manifest(self):
        try:
            if MANIFEST_PATH.exists():
                with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                    self.manifest = json.load(f)
                logger.info(f"Loaded models manifest from {MANIFEST_PATH}")
            else:
                logger.warning(f"Models manifest not found at {MANIFEST_PATH}")
        except Exception as e:
            logger.error(f"Failed to load models manifest: {e}")

    def get_model(self, path: str, default: str = "llama3.1:8b") -> str:
        """
        Retrieves a model name from the manifest using dot notation.
        Example: get_model("core_agents.chat") -> "Meta-Llama-3.1-8B-Instruct"
        """
        try:
            parts = path.split('.')
            current = self.manifest
            for part in parts:
                current = current.get(part, {})
            
            if isinstance(current, dict) and "name" in current:
                return current["name"]
            
            # If not a dict with 'name' or path fails, return default
            logger.warning(f"Model path '{path}' not found in manifest. Using default: {default}")
            return default
            
        except Exception as e:
            logger.error(f"Error resolving model path '{path}': {e}")
            return default

model_manager = ModelManager()
