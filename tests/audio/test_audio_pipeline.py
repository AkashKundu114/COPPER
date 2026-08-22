import pytest
import io
import wave
from app.services.audio_service import audio_pipeline, AudioPipelineManager


def test_audio_pipeline_manager_initialization():
    mgr = AudioPipelineManager()
    assert mgr.stt is not None
    assert mgr.tts is not None


def test_audio_pipeline_status():
    status = audio_pipeline.get_status()
    assert status["status"] == "ready"
    assert "stt_models" in status
    assert "tts_voices" in status
    assert "models_dir" in status


def test_audio_pipeline_tts_wav_validity():
    buf = audio_pipeline.tts._generate_beeps_wav(duration=0.2, freq=440.0)
    assert len(buf) > 44
    assert buf[:4] == b"RIFF"
    assert buf[8:12] == b"WAVE"


def test_audio_pipeline_silence_wav():
    buf = audio_pipeline.tts._generate_silence_wav(duration=0.1)
    assert len(buf) > 44
    with io.BytesIO(buf) as bio:
        with wave.open(bio, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getframerate() == 22050


@pytest.mark.asyncio
async def test_audio_pipeline_end_to_end_empty():
    # Calling process_voice_turn with empty bytes
    turn_gen = audio_pipeline.process_voice_turn(b"", session_id="test_session")
    events = []
    async for event in turn_gen:
        events.append(event)
    assert len(events) >= 1
    assert events[0]["type"] == "transcription"
