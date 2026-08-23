from pathlib import Path

from app.core.config import Settings, settings


def test_config_app_name():
    assert settings.APP_NAME == "COPPER"


def test_config_version():
    assert settings.APP_VERSION == "1.0.0"


def test_config_agent_tiers_count():
    assert len(settings.AGENT_TIERS) == 5


def test_config_agent_tiers_bounds():
    assert settings.AGENT_TIERS[0][1] == "Stranger"
    assert settings.AGENT_TIERS[-1][1] == "Inner Circle"


def test_config_audio_models_dir():
    assert hasattr(settings, "AUDIO_MODELS_DIR")
    assert isinstance(settings.AUDIO_MODELS_DIR, (str, Path))


def test_config_whisper_dir():
    assert hasattr(settings, "WHISPER_DIR")
    assert isinstance(settings.WHISPER_DIR, (str, Path))


def test_config_tts_dir():
    assert hasattr(settings, "TTS_DIR")
    assert isinstance(settings.TTS_DIR, (str, Path))


def test_config_database_url():
    assert hasattr(settings, "DATABASE_URL")
    assert len(settings.DATABASE_URL) > 0


def test_config_redis_url():
    assert hasattr(settings, "REDIS_URL")
    assert len(settings.REDIS_URL) > 0


def test_config_env_override():
    custom = Settings(APP_NAME="COPPER_STAGE_2")
    assert custom.APP_NAME == "COPPER_STAGE_2"
