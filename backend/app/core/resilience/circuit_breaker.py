"""Concurrency-Safe Distributed Circuit Breaker Pattern Implementation.

Protects COPPER subsystems (Ollama LLM, Vector Store, Tools, External APIs)
from cascading failures during outages.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine

from app.core.logger import logger


class CircuitState(str, Enum):
    CLOSED = "CLOSED"        # Normal operation: traffic flows through
    OPEN = "OPEN"            # Tripped: fail fast without calling target
    HALF_OPEN = "HALF_OPEN"  # Testing: allow limited canary requests


class CircuitBreakerOpenError(Exception):
    """Raised when an operation is attempted while the circuit breaker is OPEN."""

    def __init__(self, breaker_name: str, retry_after: float):
        self.breaker_name = breaker_name
        self.retry_after = retry_after
        super().__init__(
            f"Circuit breaker '{breaker_name}' is OPEN. Fast-failing request. Retry after {retry_after:.1f}s."
        )


@dataclass
class CircuitBreakerStats:
    name: str
    state: CircuitState
    failure_count: int
    success_count: int
    consecutive_failures: int
    total_tripped_count: int
    last_failure_time: float | None
    last_state_change: float


class CircuitBreaker:
    """Production asynchronous circuit breaker."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_s: float = 30.0,
        half_open_max_trials: int = 2,
    ):
        self.name = name
        self.failure_threshold = max(1, failure_threshold)
        self.recovery_timeout_s = max(0.01, recovery_timeout_s)
        self.half_open_max_trials = max(1, half_open_max_trials)

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._consecutive_failures = 0
        self._success_count = 0
        self._half_open_trials = 0
        self._total_tripped_count = 0
        self._last_failure_time: float | None = None
        self._last_state_change: float = time.time()
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        # Check if recovery timeout has elapsed while OPEN
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_state_change
            if elapsed >= self.recovery_timeout_s:
                return CircuitState.HALF_OPEN
        return self._state

    async def _transition_to(self, new_state: CircuitState) -> None:
        if self._state != new_state:
            old_state = self._state
            self._state = new_state
            self._last_state_change = time.time()
            if new_state == CircuitState.OPEN:
                self._total_tripped_count += 1
                logger.warning(
                    f"[CircuitBreaker:{self.name}] TRIPPED to OPEN after {self._consecutive_failures} failures. "
                    f"Cooling down for {self.recovery_timeout_s}s."
                )
            elif new_state == CircuitState.HALF_OPEN:
                self._half_open_trials = 0
                logger.info(f"[CircuitBreaker:{self.name}] Transitioned to HALF_OPEN. Testing recovery.")
            elif new_state == CircuitState.CLOSED:
                self._consecutive_failures = 0
                self._half_open_trials = 0
                logger.info(f"[CircuitBreaker:{self.name}] Fully recovered. Circuit CLOSED.")

    async def before_call(self) -> None:
        """Checks if a call is permissible; raises CircuitBreakerOpenError if OPEN."""
        async with self._lock:
            current = self.state
            if current == CircuitState.OPEN:
                retry_after = max(0.0, self.recovery_timeout_s - (time.time() - self._last_state_change))
                raise CircuitBreakerOpenError(self.name, retry_after)
            elif current == CircuitState.HALF_OPEN:
                if self._state != CircuitState.HALF_OPEN:
                    await self._transition_to(CircuitState.HALF_OPEN)
                self._half_open_trials += 1

    async def on_success(self) -> None:
        """Records a successful execution."""
        async with self._lock:
            self._success_count += 1
            if self._state == CircuitState.HALF_OPEN:
                if self._half_open_trials >= self.half_open_max_trials:
                    await self._transition_to(CircuitState.CLOSED)
            elif self._state == CircuitState.CLOSED:
                self._consecutive_failures = 0

    async def on_failure(self, error: Exception) -> None:
        """Records an execution failure and trips if threshold reached."""
        async with self._lock:
            self._failure_count += 1
            self._consecutive_failures += 1
            self._last_failure_time = time.time()

            if self._state == CircuitState.HALF_OPEN:
                # Canary failed in HALF_OPEN: immediately re-trip to OPEN
                await self._transition_to(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._consecutive_failures >= self.failure_threshold:
                    await self._transition_to(CircuitState.OPEN)

    async def call(self, coro_fn: Callable[[], Coroutine[Any, Any, Any]]) -> Any:
        """Executes a coroutine wrapped in the circuit breaker guard."""
        await self.before_call()
        try:
            res = await coro_fn()
            await self.on_success()
            return res
        except Exception as exc:
            await self.on_failure(exc)
            raise

    async def reset(self) -> None:
        """Manually forces the circuit breaker back to CLOSED state."""
        async with self._lock:
            await self._transition_to(CircuitState.CLOSED)
            self._consecutive_failures = 0
            self._failure_count = 0

    def get_stats(self) -> CircuitBreakerStats:
        return CircuitBreakerStats(
            name=self.name,
            state=self.state,
            failure_count=self._failure_count,
            success_count=self._success_count,
            consecutive_failures=self._consecutive_failures,
            total_tripped_count=self._total_tripped_count,
            last_failure_time=self._last_failure_time,
            last_state_change=self._last_state_change,
        )


class CircuitBreakerRegistry:
    """Global registry managing named circuit breakers."""

    def __init__(self):
        self._breakers: dict[str, CircuitBreaker] = {}
        self._lock = asyncio.Lock()

    def get_or_create(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout_s: float = 30.0,
        half_open_max_trials: int = 2,
    ) -> CircuitBreaker:
        if name not in self._breakers:
            self._breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=failure_threshold,
                recovery_timeout_s=recovery_timeout_s,
                half_open_max_trials=half_open_max_trials,
            )
        return self._breakers[name]

    def get(self, name: str) -> CircuitBreaker | None:
        return self._breakers.get(name)

    def list_all(self) -> list[CircuitBreakerStats]:
        return [b.get_stats() for b in self._breakers.values()]

    async def reset_all(self) -> None:
        for b in self._breakers.values():
            await b.reset()


circuit_breaker_registry = CircuitBreakerRegistry()
