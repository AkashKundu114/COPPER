import base64
from typing import Optional, AsyncGenerator
from app.ai.llm.prompt_manager import get_system_prompt, build_messages
from app.ai.orchestration.langchain_manager import langchain_manager
from app.core.constants import AgentType, LLMProvider
from app.core.config import settings
from app.core.logger import logger


class VisionAgent:
    async def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str = "Describe this image in detail.",
        use_openai: bool = True,
    ) -> str:
        if use_openai and settings.OPENAI_API_KEY:
            return await self._openai_vision(image_bytes, prompt)
        return await self._ollama_vision(image_bytes, prompt)

    async def _openai_vision(self, image_bytes: bytes, prompt: str) -> str:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{b64}"},
                            },
                        ],
                    }
                ],
                max_tokens=1000,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI vision error: {e}")
            raise

    async def _ollama_vision(self, image_bytes: bytes, prompt: str) -> str:
        """Use Ollama vision model (e.g. llava)."""
        import httpx
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "model": "llava",
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                    "images": [b64],
                }
            ],
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{settings.OLLAMA_HOST}/api/chat", json=payload
                )
                data = response.json()
                return data["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama vision error: {e}")
            raise

    async def run(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> str:
        system = get_system_prompt(AgentType.VISION, context)
        messages = build_messages(system, history, message)
        try:
            return await langchain_manager.ainvoke(messages, provider)
        except Exception as e:
            logger.error(f"VisionAgent error: {e}")
            raise

    async def stream(
        self,
        message: str,
        history: list[dict],
        context: str = "",
        provider: LLMProvider = LLMProvider.OLLAMA,
    ) -> AsyncGenerator[str, None]:
        system = get_system_prompt(AgentType.VISION, context)
        messages = build_messages(system, history, message)
        async for chunk in langchain_manager.astream(messages, provider):
            yield chunk


vision_agent = VisionAgent()
