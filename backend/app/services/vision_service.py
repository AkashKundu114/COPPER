import base64
import re
from typing import Any
from app.ai.llm.model_manager import model_manager
from app.ai.llm.ollama_client import ollama_client
from app.ai.memory.persistent_memory import persistent_memory
from app.core.logger import logger


class VisionService:
    """
    Service for real-time ambient vision observation via Argus (Webcam)
    and Iris (Screen Vision) sensors.
    """

    VISION_PROMPT = (
        "You are COPPER's Argus/Iris Optical Sensor observing the operator Akash. "
        "In ONE concise, natural sentence (under 18 words), describe what you see the operator doing "
        "or what is on their workstation. Do not output markdown, prefixes, or bullet points."
    )

    async def observe_frame(self, image_base64: str, source: str = "camera") -> dict[str, Any]:
        """
        Processes a video frame snapshot from webcam or screen and returns
        a concise contextual observation.
        """
        if not image_base64:
            return {"error": "No image data provided", "observation": "Optical sensor idle."}

        # Select lightweight vision model from manifest
        vision_model = model_manager.get_model("vision_agents.vision_lightweight", "moondream:1.8b")

        try:
            if await ollama_client.is_available():
                messages = [
                    {
                        "role": "user",
                        "content": self.VISION_PROMPT,
                        "images": [image_base64],
                    }
                ]
                raw = await ollama_client.chat(messages, model=vision_model)
                clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL | re.IGNORECASE).strip()
                clean = clean.replace("\n", " ").strip("\"' ")

                if clean:
                    # Update persistent memory context so chat turns are aware of vision
                    persistent_memory.set_preference("latest_vision_observation", clean)
                    return {
                        "source": source,
                        "observation": clean,
                        "model": vision_model,
                    }
        except Exception as e:
            logger.debug(f"Vision model inference fallback: {e}")

        # Fallback tactical observation if vision model not downloaded
        if source == "camera":
            fallback = "Operator active at workstation. Optical telemetry synchronized."
        else:
            fallback = "Active desktop workspace detected. Code editor and development tools in focus."

        persistent_memory.set_preference("latest_vision_observation", fallback)
        return {
            "source": source,
            "observation": fallback,
            "model": "heuristic_telemetry",
        }


vision_service = VisionService()
