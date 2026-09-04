from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "COPPER"
    APP_VERSION: str = "1.0.0"
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "tauri://localhost",
        "http://tauri.localhost",
    ]
    DB_PATH: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "copper_memory.db")
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"
    REDIS_URL: str = "redis://localhost:6379/0"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    AI_MODELS_DIR: str = str(Path(__file__).resolve().parents[3] / "ai-models")
    DOCUMENTS_DIR: str = str(Path(__file__).resolve().parent.parent.parent / "data" / "documents")
    AUDIO_MODELS_DIR: str = str(Path(__file__).resolve().parents[3] / "ai-models" / "audio")
    WHISPER_DIR: str = str(Path(__file__).resolve().parents[3] / "ai-models" / "audio" / "whisper")
    TTS_DIR: str = str(Path(__file__).resolve().parents[3] / "ai-models" / "audio" / "tts")
    AGENT_TIERS: list[tuple[int, str]] = [
        (0, "Stranger"),
        (1, "Acquaintance"),
        (3, "Regular"),
        (8, "Trusted"),
        (20, "Inner Circle"),
    ]
    RELATIONSHIP_TIERS: list[tuple[int, str]] = [
        (0, "Just Met"),
        (1, "Getting Acquainted"),
        (5, "Regular Collaborator"),
        (15, "Trusted Partner"),
        (40, "Inner Circle"),
    ]
    REFLECTION_INTERVAL_SECONDS: int = 600
    REFLECTION_CONFIDENCE_THRESHOLD: float = 0.7
    WAKE_WORD_ENGINE: str = "openwakeword"
    WAKE_WORD_MODEL_PATH: str = str(Path(__file__).resolve().parents[3] / "ai-models" / "wakeword" / "hey_copper.onnx")
    WAKE_WORD_EMBEDDING_PATH: str = str(
        Path(__file__).resolve().parents[3] / "ai-models" / "wakeword" / "embedding_model.onnx"
    )
    GATEKEEPER_KEEP_ALIVE: int = -1
    HEAVY_MODEL_IDLE_UNLOAD_SECONDS: int = 240

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
