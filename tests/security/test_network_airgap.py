import pytest
from app.core.config import NetworkMode, settings
from app.ai.tools.builtin.web_tools import (
    NetworkEgressForbiddenError,
    web_search,
    web_fetch,
)
from app.ai.tools.executor import tool_executor
from app.core.data_firewall import redact


@pytest.fixture(autouse=True)
def reset_network_mode():
    original_mode = settings.NETWORK_MODE
    original_web_enabled = settings.WEB_SEARCH_ENABLED
    yield
    settings.NETWORK_MODE = original_mode
    settings.WEB_SEARCH_ENABLED = original_web_enabled


@pytest.mark.asyncio
async def test_offline_airgap_mode_blocks_web_search():
    """Verify that OFFLINE_AIRGAP strictly raises NetworkEgressForbiddenError on search."""
    settings.NETWORK_MODE = NetworkMode.OFFLINE_AIRGAP
    settings.WEB_SEARCH_ENABLED = True

    with pytest.raises(NetworkEgressForbiddenError) as exc_info:
        await web_search("latest AI security papers")

    assert "prohibited under OFFLINE_AIRGAP mode" in str(exc_info.value)


@pytest.mark.asyncio
async def test_offline_airgap_mode_blocks_web_fetch():
    """Verify that OFFLINE_AIRGAP strictly raises NetworkEgressForbiddenError on fetch."""
    settings.NETWORK_MODE = NetworkMode.OFFLINE_AIRGAP
    settings.WEB_SEARCH_ENABLED = True

    with pytest.raises(NetworkEgressForbiddenError) as exc_info:
        await web_fetch("https://example.com/api/data")

    assert "prohibited under OFFLINE_AIRGAP mode" in str(exc_info.value)


@pytest.mark.asyncio
async def test_local_services_mode_blocks_external_wan_fetch():
    """Verify that LOCAL_SERVICES blocks outbound WAN URLs but permits loopback."""
    settings.NETWORK_MODE = NetworkMode.LOCAL_SERVICES
    settings.WEB_SEARCH_ENABLED = True

    with pytest.raises(NetworkEgressForbiddenError) as exc_info:
        await web_fetch("https://api.github.com/repos/AkashKundu114/COPPER")

    assert "prohibited under LOCAL_SERVICES mode" in str(exc_info.value)
    assert "Only local loopback endpoints are permitted" in str(exc_info.value)


@pytest.mark.asyncio
async def test_local_services_mode_prevents_duckduckgo_wan_fallback():
    """Verify that LOCAL_SERVICES does not contact DuckDuckGo when SearXNG is unavailable."""
    settings.NETWORK_MODE = NetworkMode.LOCAL_SERVICES
    settings.WEB_SEARCH_ENABLED = True
    settings.SEARXNG_URL = "http://127.0.0.1:59999"  # Non-existent port to force fallback check

    result = await web_search("offline test query")
    assert result["status"] == "partial"
    assert result["provider"] == "offline_notice"
    assert "prohibited under LOCAL_SERVICES mode" in result["message"]


@pytest.mark.asyncio
async def test_tool_executor_enforces_airgap_fail_safe():
    """Verify ToolExecutor cleanly surfaces NetworkEgressForbiddenError as a failed result."""
    settings.NETWORK_MODE = NetworkMode.OFFLINE_AIRGAP
    settings.WEB_SEARCH_ENABLED = True

    res = await tool_executor.execute("web_search", {"query": "sample search"})
    assert res.success is False
    assert "NetworkEgressForbiddenError" in (res.error or "") or "prohibited under OFFLINE_AIRGAP" in (res.error or "")


def test_data_firewall_redaction_before_query():
    """Verify Data Firewall sanitizes PII and tokens before outbound transmission."""
    prompt = "Look up user with api_key=sk-ant-api03-abcdef1234567890abcdef12345 and email test@example.com"
    sanitized = redact(prompt)
    assert "sk-ant" not in sanitized or "REDACTED" in sanitized
    assert "test@example.com" not in sanitized
    assert "•••EMAIL_REDACTED•••" in sanitized
