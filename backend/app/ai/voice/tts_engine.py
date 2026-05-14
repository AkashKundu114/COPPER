import io
from typing import Optional
from app.core.config import settings
from app.core.logger import logger


async def synthesize_speech(
    text: str,
    voice: Optional[str] = None,
    use_openai: bool = True,
) -> bytes:
    """Convert text to speech. Returns audio bytes (MP3)."""
    if use_openai and settings.OPENAI_API_KEY:
        return await _openai_tts(text, voice)
    return await _local_tts(text)


async def _openai_tts(text: str, voice: Optional[str] = None) -> bytes:
    from app.ai.llm.openai_client import openai_tts
    voice = voice or settings.TTS_VOICE
    try:
        audio_bytes = await openai_tts(text, voice)
        logger.debug(f"TTS generated {len(audio_bytes)} bytes via OpenAI")
        return audio_bytes
    except Exception as e:
        logger.error(f"OpenAI TTS error: {e}")
        raise


async def _local_tts(text: str) -> bytes:
    """Local TTS using pyttsx3 as fallback."""
    try:
        import pyttsx3
        import tempfile, os
        engine = pyttsx3.init()
        engine.setProperty("rate", 180)
        engine.setProperty("volume", 0.9)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(tmp_path)
        return audio_bytes
    except Exception as e:
        logger.error(f"Local TTS error: {e}")
        # Return empty bytes rather than crashing
        return b""


def get_available_voices() -> list[dict]:
    """Get list of available TTS voices."""
    openai_voices = [
        {"id": "alloy", "name": "Alloy", "provider": "openai"},
        {"id": "echo", "name": "Echo", "provider": "openai"},
        {"id": "fable", "name": "Fable", "provider": "openai"},
        {"id": "onyx", "name": "Onyx", "provider": "openai"},
        {"id": "nova", "name": "Nova", "provider": "openai"},
        {"id": "shimmer", "name": "Shimmer", "provider": "openai"},
    ]
    return openai_voices
