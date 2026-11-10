"""Tests for API Rate Limiting and Abuse Prevention."""

import time
import pytest
from fastapi.testclient import TestClient

from app.core.security.rate_limiter import (
    RateLimitConfig,
    SlidingWindowRateLimiter,
)
from app.main import app

client = TestClient(app)


def test_sliding_window_limiter_burst_and_sustained():
    """Verify rate limiter blocks client when burst ceiling is breached."""
    cfg = RateLimitConfig(
        default_requests_per_minute=10,
        burst_requests_per_10s=5,
        sensitive_requests_per_minute=3,
    )
    limiter = SlidingWindowRateLimiter(config=cfg)
    client_id = "test_client_ip_1"

    # First 5 calls within burst limit should succeed
    for _ in range(5):
        allowed, _ = limiter.is_allowed(client_id, is_sensitive=False)
        assert allowed is True

    # 6th call should breach burst limit (5 per 10s)
    allowed, retry_after = limiter.is_allowed(client_id, is_sensitive=False)
    assert allowed is False
    assert retry_after > 0


def test_sensitive_endpoint_rate_limit():
    """Verify sensitive endpoints have tighter rate limits."""
    cfg = RateLimitConfig(
        default_requests_per_minute=20,
        burst_requests_per_10s=10,
        sensitive_requests_per_minute=2,
    )
    limiter = SlidingWindowRateLimiter(config=cfg)
    client_id = "test_client_ip_sensitive"

    # First 2 sensitive calls succeed
    allowed1, _ = limiter.is_allowed(client_id, is_sensitive=True)
    allowed2, _ = limiter.is_allowed(client_id, is_sensitive=True)
    assert allowed1 is True
    assert allowed2 is True

    # 3rd sensitive call breaches quota
    allowed3, retry_after = limiter.is_allowed(client_id, is_sensitive=True)
    assert allowed3 is False
    assert retry_after > 0


def test_health_check_exempt_from_rate_limiting():
    """Verify monitoring endpoints (/health) are never throttled."""
    for _ in range(15):
        res = client.get("/health")
        assert res.status_code == 200
