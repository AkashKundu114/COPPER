from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "COPPER"
    ALLOWED_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    DB_PATH: str = str(Path(__file__).resolve().parent.parent / "data" / "copper_memory.db")

    # Familiarity tier thresholds (per-agent invocation counts)
    AGENT_TIERS: list[tuple[int, str]] = [
        (0, "Stranger"),
        (1, "Acquaintance"),
        (3, "Regular"),
        (8, "Trusted"),
        (20, "Inner Circle"),
    ]

    # Overall relationship tier thresholds (total interactions across all agents)
    RELATIONSHIP_TIERS: list[tuple[int, str]] = [
        (0, "Just Met"),
        (1, "Getting Acquainted"),
        (5, "Regular Collaborator"),
        (15, "Trusted Partner"),
        (40, "Inner Circle"),
    ]

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
