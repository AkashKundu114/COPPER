"""API Rate Limiting and Abuse Prevention Middleware.

Protects local COPPER services, Ollama hot-swap queues, and database engines
from request flooding, memory exhaustion, and brute-force abuse.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.logger import logger


@dataclass
class RateLimitConfig:
    default_requests_per_minute: int = 120
    burst_requests_per_10s: int = 35
    sensitive_requests_per_minute: int = 20


class SlidingWindowRateLimiter:
    """In-memory sliding window rate limiter tracking per-client timestamps."""

    def __init__(self, config: RateLimitConfig | None = None):
        self.config = config or RateLimitConfig()
        self._minute_windows: dict[str, deque[float]] = defaultdict(deque)
        self._ten_sec_windows: dict[str, deque[float]] = defaultdict(deque)

    def is_allowed(self, client_key: str, is_sensitive: bool = False) -> tuple[bool, int]:
        """Checks whether client is within quota. Returns (allowed, retry_after_seconds)."""
        now = time.time()
        one_min_ago = now - 60.0
        ten_sec_ago = now - 10.0

        # Purge expired timestamps
        min_deque = self._minute_windows[client_key]
        while min_deque and min_deque[0] < one_min_ago:
            min_deque.popleft()

        burst_deque = self._ten_sec_windows[client_key]
        while burst_deque and burst_deque[0] < ten_sec_ago:
            burst_deque.popleft()

        limit_min = (
            self.config.sensitive_requests_per_minute
            if is_sensitive
            else self.config.default_requests_per_minute
        )

        if len(min_deque) >= limit_min:
            retry_after = max(1, int(60 - (now - min_deque[0])))
            return False, retry_after

        if len(burst_deque) >= self.config.burst_requests_per_10s:
            retry_after = max(1, int(10 - (now - burst_deque[0])))
            return False, retry_after

        min_deque.append(now)
        burst_deque.append(now)
        return True, 0


rate_limiter = SlidingWindowRateLimiter()


class RateLimiterMiddleware(BaseHTTPMiddleware):
    """Starlette middleware intercepting high-frequency request floods."""

    SENSITIVE_PATHS = {
        "/api/v1/audit/delete-all",
        "/api/v1/agents/activate",
        "/api/v1/chat/message",
        "/api/v1/guardian/confirm",
        "/api/v1/system/restart",
    }

    EXEMPT_PATHS = {
        "/health",
        "/",
        "/docs",
        "/openapi.json",
        "/redoc",
    }

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in self.EXEMPT_PATHS or path.startswith("/static") or path.startswith("/generated"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        if client_ip == "testclient" or os.environ.get("PYTEST_CURRENT_TEST"):
            return await call_next(request)

        is_sensitive = path in self.SENSITIVE_PATHS

        allowed, retry_after = rate_limiter.is_allowed(client_ip, is_sensitive=is_sensitive)
        if not allowed:
            logger.warning(f"[RateLimiter] Throttling request from {client_ip} to {path} (retry in {retry_after}s)")
            return JSONResponse(
                status_code=429,
                content={
                    "status": "error",
                    "error": "Too Many Requests",
                    "message": f"Rate limit exceeded. Please retry after {retry_after} seconds.",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )

        response: Response = await call_next(request)
        return response
