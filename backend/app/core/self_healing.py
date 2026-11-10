"""Self-Healing Engine with Exponential Jitter, Circuit Breaking & Dead-Letter Routing."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.resilience.backoff import calculate_backoff
from app.core.resilience.circuit_breaker import (
    CircuitBreakerOpenError,
    circuit_breaker_registry,
)
from app.core.resilience.dead_letter_queue import dead_letter_queue


@dataclass
class RecoveryAttempt:
    strategy: str
    succeeded: bool
    error: str | None = None


@dataclass
class ResilientResult:
    success: bool
    result: Any = None
    attempts: list[RecoveryAttempt] = field(default_factory=list)
    final_error: str | None = None
    circuit_broken: bool = False


async def resilient_call(
    primary: Callable[[], Awaitable[Any]],
    *,
    fallbacks: list[Callable[[], Awaitable[Any]]] | None = None,
    retries: int = 1,
    retry_delay_s: float = 0.5,
    max_delay_s: float = 30.0,
    exponential_backoff: bool = True,
    timeout_s: float | None = None,
    circuit_breaker_name: str | None = None,
    circuit_failure_threshold: int = 5,
    circuit_recovery_timeout_s: float = 30.0,
    db: Session | None = None,
    session_id: str | None = None,
    actor: str = "system",
    incident_label: str = "operation",
    enable_dlq: bool = False,
    task_id: str | None = None,
    dlq_payload: dict[str, Any] | None = None,
) -> ResilientResult:
    """Executes primary coroutine with bounded retries, exponential jitter, circuit breakers, and fallbacks."""
    if primary is None:
        return ResilientResult(success=False, final_error="Primary callable is required")

    safe_retries = max(0, retries)
    safe_retry_delay = max(0.0, retry_delay_s)
    attempts: list[RecoveryAttempt] = []

    # 1. Circuit breaker lookup if specified
    breaker = None
    if circuit_breaker_name:
        breaker = circuit_breaker_registry.get_or_create(
            name=circuit_breaker_name,
            failure_threshold=circuit_failure_threshold,
            recovery_timeout_s=circuit_recovery_timeout_s,
        )

    # 2. Primary execution with retries
    circuit_tripped = False
    for attempt_num in range(safe_retries + 1):
        if breaker:
            try:
                await breaker.before_call()
            except CircuitBreakerOpenError as cb_err:
                circuit_tripped = True
                attempts.append(
                    RecoveryAttempt(strategy=f"circuit_breaker:{circuit_breaker_name}", succeeded=False, error=str(cb_err))
                )
                logger.warning(f"[self-healing] Circuit open for {incident_label}: {cb_err}")
                break

        try:
            if timeout_s is not None and timeout_s > 0:
                result = await asyncio.wait_for(primary(), timeout=timeout_s)
            else:
                result = await primary()

            if breaker:
                await breaker.on_success()

            attempts.append(RecoveryAttempt(strategy=f"primary (attempt {attempt_num + 1})", succeeded=True))
            _log_incident(db, session_id, actor, incident_label, attempts, recovered=True)
            return ResilientResult(success=True, result=result, attempts=attempts)

        except Exception as e:
            if breaker:
                await breaker.on_failure(e)

            attempts.append(
                RecoveryAttempt(strategy=f"primary (attempt {attempt_num + 1})", succeeded=False, error=str(e))
            )
            logger.warning(f"[self-healing] {incident_label} failed (attempt {attempt_num + 1}): {e}")

            if attempt_num < safe_retries:
                if exponential_backoff:
                    delay = calculate_backoff(attempt_num, base_delay_s=safe_retry_delay, max_delay_s=max_delay_s)
                else:
                    delay = safe_retry_delay
                await asyncio.sleep(delay)

    # 3. Fallbacks execution
    for i, fallback in enumerate(fallbacks or []):
        try:
            if timeout_s is not None and timeout_s > 0:
                result = await asyncio.wait_for(fallback(), timeout=timeout_s)
            else:
                result = await fallback()

            attempts.append(RecoveryAttempt(strategy=f"fallback[{i}]", succeeded=True))
            _log_incident(db, session_id, actor, incident_label, attempts, recovered=True)
            return ResilientResult(success=True, result=result, attempts=attempts)
        except Exception as e:
            attempts.append(RecoveryAttempt(strategy=f"fallback[{i}]", succeeded=False, error=str(e)))
            logger.warning(f"[self-healing] {incident_label} fallback[{i}] failed: {e}")

    final_error = attempts[-1].error if attempts else "unknown error"
    _log_incident(db, session_id, actor, incident_label, attempts, recovered=False)

    # 4. Dead-letter queue routing if enabled
    if enable_dlq:
        tid = task_id or session_id or incident_label
        payload = dlq_payload or {"incident_label": incident_label, "actor": actor}
        dead_letter_queue.enqueue(
            task_id=tid,
            origin_service=actor,
            failure_reason=final_error or "Unknown failure",
            payload=payload,
            attempts_count=len(attempts),
        )

    return ResilientResult(
        success=False,
        attempts=attempts,
        final_error=final_error,
        circuit_broken=circuit_tripped,
    )


def _log_incident(
    db: Session | None,
    session_id: str | None,
    actor: str,
    label: str,
    attempts: list[RecoveryAttempt],
    recovered: bool,
) -> None:
    if db is None:
        return
    try:
        from app.services.guardian_service import guardian_service

        status = "Recovered" if recovered else "Failed after all recovery strategies"
        detail_lines = [f"{a.strategy}: {('ok' if a.succeeded else a.error)}" for a in attempts]
        guardian_service.log(
            db=db,
            category="tool_executed" if recovered else "guardian_challenge",
            actor=actor,
            summary=f"[self-healing] {label}: {status}",
            detail="\n".join(detail_lines),
            session_id=session_id,
        )
    except Exception as e:
        logger.debug(f"[self-healing] Failed to record guardian incident: {e}")


class SelfHealingEngine:
    """Enterprise reliability coordinator for COPPER."""

    def __init__(self):
        self.circuit_breakers = circuit_breaker_registry
        self.dlq = dead_letter_queue

    async def execute(
        self,
        primary: Callable[[], Awaitable[Any]],
        *,
        fallbacks: list[Callable[[], Awaitable[Any]]] | None = None,
        retries: int = 2,
        timeout_s: float | None = 30.0,
        circuit_breaker_name: str | None = None,
        enable_dlq: bool = False,
        task_id: str | None = None,
        incident_label: str = "operation",
        actor: str = "system",
    ) -> ResilientResult:
        return await resilient_call(
            primary=primary,
            fallbacks=fallbacks,
            retries=retries,
            timeout_s=timeout_s,
            circuit_breaker_name=circuit_breaker_name,
            enable_dlq=enable_dlq,
            task_id=task_id,
            incident_label=incident_label,
            actor=actor,
        )


self_healing_engine = SelfHealingEngine()
