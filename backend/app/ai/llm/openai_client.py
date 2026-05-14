from typing import AsyncGenerator, Optional
from openai import AsyncOpenAI
from app.core.config import settings
from app.core.logger import logger

_client: Optional[AsyncOpenAI] = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


async def openai_chat(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> str:
    client = get_openai_client()
    model = model or settings.OPENAI_MODEL
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenAI chat error: {e}")
        raise


async def openai_stream_chat(
    messages: list[dict],
    model: Optional[str] = None,
    temperature: float = 0.7,
) -> AsyncGenerator[str, None]:
    client = get_openai_client()
    model = model or settings.OPENAI_MODEL
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        logger.error(f"OpenAI stream error: {e}")
        raise


async def openai_transcribe(audio_bytes: bytes, filename: str = "audio.wav") -> str:
    client = get_openai_client()
    try:
        import io
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = filename
        transcript = await client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
        return transcript.text
    except Exception as e:
        logger.error(f"OpenAI transcribe error: {e}")
        raise


async def openai_tts(text: str, voice: str = None) -> bytes:
    client = get_openai_client()
    voice = voice or settings.TTS_VOICE
    try:
        response = await client.audio.speech.create(
            model=settings.TTS_MODEL,
            voice=voice,
            input=text,
        )
        return response.content
    except Exception as e:
        logger.error(f"OpenAI TTS error: {e}")
        raise
