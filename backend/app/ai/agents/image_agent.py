import urllib.parse
import urllib.request
from pathlib import Path

from app.ai.agents.base import BaseAgent
from app.core.constants import AgentType, LLMProvider


class ImageAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_type=AgentType.IMAGE,
            name="PICASSO (Image Generation Agent)",
            description="Generates AI images and visual assets.",
        )
        self.output_dir = Path(__file__).parent.parent.parent.parent.parent / "frontend" / "public" / "generated"
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

        safe_prompt = urllib.parse.quote(prompt)
        # Using Pollinations AI for free, fast, high-quality SDXL generation
        api_url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width=1024&height=1024&nologo=true"

        return (
            f"🎨 **Generated Image for:** `{prompt}`\n\n"
            f"![{prompt}]({api_url})\n\n"
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
