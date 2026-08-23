import io
import wave

import pytest
from app.services.audio_service import WhisperSTTPipeline


def test_stt_initialization():
    stt = WhisperSTTPipeline()
    assert stt.models_dir.exists()


def test_stt_list_available_models():
    stt = WhisperSTTPipeline()
    models = stt.list_available_models()
    assert isinstance(models, list)


@pytest.mark.asyncio
async def test_stt_transcribe_empty():
    stt = WhisperSTTPipeline()
    res = await stt.transcribe(b"")
    assert isinstance(res, dict)
    assert "text" in res
    assert "engine" in res


@pytest.mark.asyncio
async def test_stt_transcribe_synthetic_pcm():
    stt = WhisperSTTPipeline()
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 8000)
    res = await stt.transcribe(buf.getvalue())
    assert "text" in res
    assert "engine" in res
