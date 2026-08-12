"""
Self-healing wrapper. Master System Prompt §12 (Self-Healing) and
Master UI Prompt §22 (Self-Healing Center).

Recovery sequence: diagnose -> retry -> alternative tool -> alternative
model -> alternative agent -> surface to user. Every attempt is recorded
via guardian_service.log() so the Self-Healing Center shows real incidents,
never fabricated status.
"""
import asyncio
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional
from sqlalchemy.orm import Session
from app.core.logger import logger


@dataclass
class RecoveryAttempt:
    strategy: str
    succeeded: bool
    error: Optional[str] = None


@dataclass
class ResilientResult:
    success: bool
    result: Any = None
    attempts: list[RecoveryAttempt] = field(default_factory=list)
    final_error: Optional[str] = None


async def resilient_call(
    primary: Callable[[], Awaitable[Any]],
    *,
    fallbacks: Optional[list[Callable[[], Awaitable[Any]]]] = None,
    retries: int = 1,
    retry_delay_s: float = 0.5,
    db: Optional[Session] = None,
    session_id: Optional[str] = None,
    actor: str = "system",
    incident_label: str = "operation",
) -> ResilientResult:
    """
    Runs `primary`, retrying `retries` times, then falling through
    `fallbacks` in order (e.g. alternative tool, alternative model,
    alternative agent — pass them pre-bound as zero-arg callables).
    Never raises — returns a ResilientResult so callers can decide how to
    surface a total failure to the user (never hide it, per §12).
    """
    attempts: list[RecoveryAttempt] = []

    for attempt_num in range(retries + 1):
        try:
            result = await primary()
            attempts.append(RecoveryAttempt(strategy=f"primary (attempt {attempt_num + 1})", succeeded=True))
            _log_incident(db, session_id, actor, incident_label, attempts, recovered=True)
            return ResilientResult(success=True, result=result, attempts=attempts)
        except Exception as e:
            attempts.append(RecoveryAttempt(
                strategy=f"primary (attempt {attempt_num + 1})", succeeded=False, error=str(e)
            ))
            logger.warning(f"[self-healing] {incident_label} failed (attempt {attempt_num + 1}): {e}")
            if attempt_num < retries:
                await asyncio.sleep(retry_delay_s)

    for i, fallback in enumerate(fallbacks or []):
        try:
            result = await fallback()
            attempts.append(RecoveryAttempt(strategy=f"fallback[{i}]", succeeded=True))
            _log_incident(db, session_id, actor, incident_label, attempts, recovered=True)
            return ResilientResult(success=True, result=result, attempts=attempts)
        except Exception as e:
            attempts.append(RecoveryAttempt(strategy=f"fallback[{i}]", succeeded=False, error=str(e)))
            logger.warning(f"[self-healing] {incident_label} fallback[{i}] failed: {e}")

    final_error = attempts[-1].error if attempts else "unknown error"
    _log_incident(db, session_id, actor, incident_label, attempts, recovered=False)
    return ResilientResult(success=False, attempts=attempts, final_error=final_error)


def _log_incident(
    db: Optional[Session],
    session_id: Optional[str],
    actor: str,
    label: str,
    attempts: list[RecoveryAttempt],
    recovered: bool,
) -> None:
    if db is None:
        return
    from app.services.guardian_service import guardian_service
    status = "Recovered" if recovered else "Failed after all recovery strategies"
    detail_lines = [f"{a.strategy}: {'ok' if a.succeeded else a.error}" for a in attempts]
    guardian_service.log(
        db=db,
        category="tool_executed" if recovered else "guardian_challenge",
        actor=actor,
        summary=f"[self-healing] {label}: {status}",
        detail="\n".join(detail_lines),
        session_id=session_id,
    )
