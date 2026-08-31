
import pytest
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


def test_format_spoken_summary_short_text():
    tts = PiperTTSPipeline()
    short = "I have updated the settings for you."
    res = tts.format_spoken_summary(short)
    assert res == "I have updated the settings for you."


def test_format_spoken_summary_long_text():
    tts = PiperTTSPipeline()
    long_text = (
        "Here is the system architecture overview.\n\n"
        "1. The database layer uses SQLite with SQLAlchemy.\n"
        "2. The cache layer uses Redis for session storage.\n"
        "3. The AI orchestrator manages multi-agent handoffs.\n\n"
        "In conclusion, the architecture is decoupled and modular."
    )
    res = tts.format_spoken_summary(long_text)
    assert "Here is the system architecture overview." in res
    assert "screen" in res.lower()
    assert "1. The database layer" not in res


def test_format_spoken_summary_with_code_block():
    tts = PiperTTSPipeline()
    code_text = (
        "I've written the Fibonacci function.\n\n"
        "```python\n"
        "def fib(n):\n"
        "    return n if n <= 1 else fib(n-1) + fib(n-2)\n"
        "```\n\n"
        "You can run it in your terminal."
    )
    res = tts.format_spoken_summary(code_text)
    assert "def fib(n)" not in res
    assert "screen" in res.lower()

