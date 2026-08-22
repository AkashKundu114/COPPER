import pytest
from app.services.audio_service import audio_pipeline, WhisperSTTPipeline, PiperTTSPipeline


def test_audio_pipeline_status():
    status = audio_pipeline.get_status()
    assert status["status"] == "ready"
    assert "stt_models" in status
    assert "tts_voices" in status
    assert len(status["tts_voices"]) >= 2


def test_tts_voices_list():
    tts = PiperTTSPipeline()
    voices = tts.list_available_voices()
    voice_ids = [v["id"] for v in voices]
    assert "os_default" in voice_ids
    assert "copper_synth" in voice_ids


@pytest.mark.asyncio
async def test_tts_synthesis_wav_generation():
    tts = PiperTTSPipeline()
    audio_bytes = await tts.synthesize("Hello, C.O.P.P.E.R audio pipeline test.")
    assert len(audio_bytes) > 44  # Valid WAV header + PCM frames
    assert audio_bytes[:4] == b"RIFF"
    assert audio_bytes[8:12] == b"WAVE"


@pytest.mark.asyncio
async def test_stt_transcription_empty():
    stt = WhisperSTTPipeline()
    res = await stt.transcribe(b"")
    assert "text" in res
    assert "engine" in res
