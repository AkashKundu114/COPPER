"""Tests for Network Security Policy, SSRF Defense, and Egress Isolation."""

import pytest

from app.ai.tools.builtin.web_tools import web_fetch
from app.core.config import NetworkMode, settings
from app.core.security.network_policy import (
    NetworkSecurityPolicy,
    SSRFViolationError,
    network_security_policy,
)


def test_ssrf_blocks_cloud_metadata_ip():
    """Verify that cloud metadata IP (169.254.169.254) is blocked unconditionally."""
    with pytest.raises(SSRFViolationError, match="Prohibited cloud metadata|protected link-local"):
        network_security_policy.validate_url("http://169.254.169.254/latest/meta-data/")


def test_ssrf_blocks_cloud_metadata_hostname():
    """Verify metadata.google.internal hostname is blocked."""
    with pytest.raises(SSRFViolationError, match="Prohibited cloud metadata"):
        network_security_policy.validate_url("http://metadata.google.internal/computeMetadata/v1/")


def test_ssrf_blocks_private_subnets_in_egress_mode(monkeypatch):
    """Verify outbound requests to private RFC1918 intranet IPs are blocked in egress mode."""
    monkeypatch.setattr(settings, "NETWORK_MODE", NetworkMode.USER_AUTHORIZED_EGRESS)

    private_urls = [
        "http://10.0.0.1:8080/admin",
        "http://192.168.1.1/router",
        "http://172.16.0.5/internal",
    ]
    for url in private_urls:
        with pytest.raises(SSRFViolationError, match="private intranet IP|SSRF Protection"):
            network_security_policy.validate_url(url)


def test_network_mode_airgap_blocks_all_egress(monkeypatch):
    """Verify OFFLINE_AIRGAP strictly blocks all requests."""
    monkeypatch.setattr(settings, "NETWORK_MODE", NetworkMode.OFFLINE_AIRGAP)

    with pytest.raises(SSRFViolationError, match="OFFLINE_AIRGAP"):
        network_security_policy.validate_url("https://example.com")


def test_network_mode_local_services_allows_loopback_only(monkeypatch):
    """Verify LOCAL_SERVICES allows 127.0.0.1 but blocks public WAN."""
    monkeypatch.setattr(settings, "NETWORK_MODE", NetworkMode.LOCAL_SERVICES)

    # 127.0.0.1 loopback should be permitted
    allowed_url = network_security_policy.validate_url("http://127.0.0.1:8888/search")
    assert allowed_url == "http://127.0.0.1:8888/search"

    # Public WAN should be blocked
    with pytest.raises(SSRFViolationError, match="LOCAL_SERVICES mode"):
        network_security_policy.validate_url("https://example.com")


@pytest.mark.asyncio
async def test_web_fetch_integrates_ssrf_protection():
    """Verify web_fetch returns network policy error when SSRF is attempted."""
    res = await web_fetch("http://169.254.169.254/credentials")
    assert res["status"] == "error"
    assert "Network policy blocked request" in res["message"]
