"""Self-Healing & Resilience Recovery Coordinator for C.O.P.P.E.R.

Orchestrates automated retry with exponential jitter, circuit breaker gating,
dead-letter queue routing, and self-healing degraded mode fallbacks.
"""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, TypeVar

from app.core.logger import logger
from app.core.resilience.backoff import calculate_backoff
from app.core.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitBreakerRegistry,
    circuit_breaker_registry,
)
from app.core.resilience.dead_letter_queue import DeadLetterQueue, dead_letter_queue

T = TypeVar("T")


class SelfHealingCoordinator:
    """Supervises task execution with circuit breaking, retries, and dead-letter routing."""

    def __init__(
        self,
        breaker_registry: CircuitBreakerRegistry = circuit_breaker_registry,
        dlq: DeadLetterQueue = dead_letter_queue,
        initial_delay_sec: float = 0.05,
        max_delay_sec: float = 1.0,
    ):
        self.breaker_registry = breaker_registry
        self.dlq = dlq
        self.base_delay = initial_delay_sec
        self.max_delay = max_delay_sec

    async def execute_resiliently(
        self,
        operation_name: str,
        coro_fn: Callable[[], Coroutine[Any, Any, T]],
        fallback_fn: Callable[[], Coroutine[Any, Any, T]] | None = None,
        max_retries: int = 3,
        circuit_service_name: str | None = None,
        task_id: str | None = None,
        payload: Any = None,
    ) -> tuple[T | None, bool, str | None]:
        """Executes a coroutine with circuit breaker, retries, fallback, and DLQ routing.
        
        Returns:
            tuple of (result, succeeded, failure_reason)
        """
        service = circuit_service_name or operation_name
        breaker = self.breaker_registry.get_or_create(service, failure_threshold=2, recovery_timeout_s=1.0)

        # 1. Check circuit breaker state
        try:
            await breaker.before_call()
        except CircuitBreakerOpenError as c_err:
            logger.warning(
                f"[SelfHealingCoordinator] Circuit '{service}' is OPEN. Rejecting immediate execution."
            )
            if fallback_fn:
                logger.info(f"[SelfHealingCoordinator] Executing fallback for '{operation_name}'")
                fallback_res = await fallback_fn()
                return fallback_res, True, None
            
            # Enqueue to DLQ
            self.dlq.enqueue(
                task_id=task_id or f"failed_{operation_name}",
                origin_service=service,
                failure_reason=str(c_err),
                payload={"service": service, "operation": operation_name, "data": str(payload)[:200]},
                error_type="CircuitBreakerOpenError",
                attempts_count=0,
            )
            return None, False, f"Circuit breaker OPEN for {service}"

        # 2. Execute with retry & backoff
        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                res = await coro_fn()
                await breaker.on_success()
                return res, True, None
            except Exception as exc:
                last_error = exc
                await breaker.on_failure(exc)
                logger.warning(
                    f"[SelfHealingCoordinator] Attempt {attempt}/{max_retries} failed for '{operation_name}': {exc}"
                )
                if attempt < max_retries:
                    delay = calculate_backoff(attempt, base_delay_s=self.base_delay, max_delay_s=self.max_delay)
                    await asyncio.sleep(delay)

        # 3. All retries exhausted
        logger.error(
            f"[SelfHealingCoordinator] Exhausted {max_retries} attempts for '{operation_name}': {last_error}"
        )

        if fallback_fn:
            logger.info(f"[SelfHealingCoordinator] Executing fallback after retries for '{operation_name}'")
            try:
                fallback_res = await fallback_fn()
                return fallback_res, True, None
            except Exception as fb_exc:
                logger.error(f"[SelfHealingCoordinator] Fallback also failed: {fb_exc}")

        # 4. Route to Dead Letter Queue
        self.dlq.enqueue(
            task_id=task_id or f"exhausted_{operation_name}",
            origin_service=service,
            failure_reason=str(last_error),
            payload={"operation": operation_name, "error": str(last_error), "payload": str(payload)[:200]},
            error_type="RetryExhaustedError",
            attempts_count=max_retries,
        )

        return None, False, str(last_error)


self_healing_coordinator = SelfHealingCoordinator()
