import asyncio
from pathlib import Path

from app.ai.agents.base import BaseAgent
from app.ai.image.diffusion_engine import diffusion_engine
from app.core.config import settings
from app.core.constants import AgentType, LLMProvider


class ImageAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.IMAGE,
            name="PICASSO (Image Generation Agent)",
            description="Generates AI images and visual assets locally using Stable Diffusion.",
        )
        self.output_dir = Path(settings.IMAGE_OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.engine = diffusion_engine

    def extract_prompt(self, message: str) -> str:
        # Simple extraction: remove command words
        lower = message.lower()
        prefixes = [
            "generate an image of",
            "generate a picture of",
            "generate a photo of",
            "generate image of",
            "draw an image of",
            "draw a picture of",
            "draw a",
            "draw me a",
            "create an image of",
            "create a picture of",
            "create a photo of",
            "make an image of",
            "make a picture of",
            "make a photo of",
            "make a",
            "generate a wallpaper of",
            "generate wallpaper of",
            "generate",
            "create",
            "draw",
        ]
        prompt = message
        for p in prefixes:
            if lower.startswith(p):
                prompt = message[len(p) :].strip()
                # Remove leading 'a' or 'an' if it was part of the remaining text
                if prompt.lower().startswith("an "):
                    prompt = prompt[3:]
                elif prompt.lower().startswith("a "):
                    prompt = prompt[2:]
                break
        return prompt.strip()

    async def run(
        self,
        message: str,
        history: list = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ) -> str:
        prompt = self.extract_prompt(message)
        if not prompt:
            prompt = "a futuristic cyber city"

        # Execute generation in worker thread to prevent event loop starvation
        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, self.engine.generate, prompt)

        engine_title = (
            "Local Stable Diffusion (SD-Turbo)"
            if res.get("engine") == "sd_turbo_local"
            else "Local Studio Canvas (Offline)"
        )
        device_str = res.get("device", "local").upper()
        steps = res.get("steps", 1)

        return (
            f"🎨 **Generated Image for:** `{prompt}`\n\n"
            f"![{prompt}]({res['url']})\n\n"
            f"⚡ **Engine:** `{engine_title}` | **Device:** `{device_str}` | **Steps:** `{steps}` | **100% Offline**\n\n"
            f"*Right-click the image and select 'Save image as...' if you wish to keep it.*"
        )

    async def stream(
        self,
        message: str,
        history: list = None,
        memory_context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
        *args,
        **kwargs,
    ):
        result = await self.run(message)
        yield result


image_agent = ImageAgent()
