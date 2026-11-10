import asyncio
import pytest

from app.core.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)


@pytest.mark.asyncio
async def test_circuit_breaker_transitions():
    """Verify CLOSED -> OPEN -> HALF_OPEN -> CLOSED transition lifecycle."""
    cb = CircuitBreaker("test_breaker", failure_threshold=2, recovery_timeout_s=0.2, half_open_max_trials=1)
    assert cb.state == CircuitState.CLOSED

    # Failure 1
    with pytest.raises(ValueError):
        async def failing():
            raise ValueError("Test error 1")
        await cb.call(failing)
    assert cb.state == CircuitState.CLOSED

    # Failure 2: reaches threshold -> trips to OPEN
    with pytest.raises(ValueError):
        async def failing2():
            raise ValueError("Test error 2")
        await cb.call(failing2)
    assert cb.state == CircuitState.OPEN

    # Fast-fail while OPEN
    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        await cb.call(lambda: asyncio.sleep(0.01))
    assert "is OPEN" in str(exc_info.value)

    # Wait for recovery timeout
    await asyncio.sleep(0.25)
    assert cb.state == CircuitState.HALF_OPEN

    # Canary trial succeeds -> transitions back to CLOSED
    async def ok():
        return "success"
    res = await cb.call(ok)
    assert res == "success"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure_re_trips():
    """Verify failure during HALF_OPEN immediately re-trips circuit to OPEN."""
    cb = CircuitBreaker("test_canary_fail", failure_threshold=1, recovery_timeout_s=0.1)

    async def fail_now():
        raise RuntimeError("simulated error")

    # Trip to OPEN
    with pytest.raises(RuntimeError):
        await cb.call(fail_now)
    assert cb.state == CircuitState.OPEN

    # Wait for cool-down
    await asyncio.sleep(0.15)
    assert cb.state == CircuitState.HALF_OPEN

    # Canary fails
    with pytest.raises(RuntimeError):
        await cb.call(fail_now)

    assert cb.state == CircuitState.OPEN
