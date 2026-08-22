import pytest
import io
import wave
from app.services.audio_service import PiperTTSPipeline


def test_tts_initialization():
    tts = PiperTTSPipeline()
    assert tts.models_dir.exists()


def test_tts_list_available_voices():
    tts = PiperTTSPipeline()
    voices = tts.list_available_voices()
    assert len(voices) >= 2
    voice_ids = [v["id"] for v in voices]
    assert "os_default" in voice_ids
    assert "copper_synth" in voice_ids


@pytest.mark.asyncio
async def test_tts_synthesize_clean_text():
    tts = PiperTTSPipeline()
    audio = await tts.synthesize("Hello world from unit test")
    assert len(audio) > 44
    assert audio[:4] == b"RIFF"
    assert audio[8:12] == b"WAVE"


@pytest.mark.asyncio
async def test_tts_synthesize_empty_string():
    tts = PiperTTSPipeline()
    audio = await tts.synthesize("   ")
    assert len(audio) > 44
    assert audio[:4] == b"RIFF"


@pytest.mark.asyncio
async def test_tts_synthesize_with_speed():
    tts = PiperTTSPipeline()
    audio = await tts.synthesize("Fast voice output", speed=1.5)
    assert len(audio) > 44
