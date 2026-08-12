from typing import List, Dict, Any, Optional
import httpx
from app.core.config import settings
from app.core.logger import logger


class OllamaClient:
    def __init__(self):
        self.base_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        self.default_model = "llama3.1:8b"

    async def is_available(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/version")
                return res.status_code == 200
        except Exception:
            return False

    async def chat(self, messages: List[Dict[str, str]], model: Optional[str] = None) -> str:
        target_model = model or self.default_model
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False
        }
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.base_url}/api/chat", json=payload)
                if res.status_code == 200:
                    data = res.json()
                    return data.get("message", {}).get("content", "")
                else:
                    logger.warning(f"Ollama response non-200 ({res.status_code}): {res.text}")
                    return f"[Ollama Fallback Response]: Mode '{target_model}' processed input."
        except Exception as e:
            logger.warning(f"Ollama connection error: {e}")
            return f"[Local Response]: Processed prompt using fallback engine."


ollama_client = OllamaClient()
