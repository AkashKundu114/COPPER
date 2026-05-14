import io
import tempfile
import os
from typing import Optional
from app.core.config import settings
from app.core.logger import logger

_model = None


def get_whisper_model():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
            _model = WhisperModel(
                settings.WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
            )
            logger.info(f"Whisper model loaded: {settings.WHISPER_MODEL}")
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            raise
    return _model


async def transcribe_audio(audio_bytes: bytes, language: Optional[str] = None) -> str:
    """Transcribe audio bytes to text using faster-whisper."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        model = get_whisper_model()
        kwargs = {"beam_size": 5}
        if language:
            kwargs["language"] = language

        segments, info = model.transcribe(tmp_path, **kwargs)
        text = " ".join(segment.text.strip() for segment in segments)
        logger.info(f"Transcribed ({info.language}): {text[:80]}...")
        return text.strip()
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        raise
    finally:
        os.unlink(tmp_path)


async def transcribe_file(file_path: str) -> str:
    with open(file_path, "rb") as f:
        return await transcribe_audio(f.read())
