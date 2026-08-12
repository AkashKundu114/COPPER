from app.core.config import Settings

def test_default_settings():
    settings = Settings()
    assert settings.APP_NAME == "COPPER"
    assert settings.APP_VERSION == "1.0.0"

def test_agent_tiers_ordering():
    settings = Settings()
    tiers = settings.AGENT_TIERS
    assert len(tiers) == 5
    assert tiers[0][1] == "Stranger"
    assert tiers[-1][1] == "Inner Circle"
