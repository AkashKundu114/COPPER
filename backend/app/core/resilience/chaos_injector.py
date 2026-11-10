"""Chaos Engineering & Fault Injection Simulator for C.O.P.P.E.R.

Injects synthetic latency spikes, connection drops, and process crashes
to verify that circuit breaking, exponential jitter backoff, and dead-letter
routing withstand production stress without catastrophic degradation.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine

from app.core.logger import logger
from app.core.resilience.circuit_breaker import CircuitBreakerRegistry
from app.core.resilience.dead_letter_queue import DeadLetterQueue
from app.core.resilience.self_healing_coordinator import SelfHealingCoordinator


class ChaosFaultType(str, Enum):
    LATENCY_SPIKE = "latency_spike"
    CONNECTION_DROP = "connection_drop"
    PROCESS_CRASH = "process_crash"
    CORRUPTED_PAYLOAD = "corrupted_payload"


@dataclass
class ChaosSimulationResult:
    fault_type: ChaosFaultType
    circuit_tripped: bool
    fallback_activated: bool
    dlq_enqueued: bool
    total_duration_ms: float
    recovered: bool
    error_summary: str | None = None


class ChaosFaultInjector:
    """Simulates infrastructure failures to validate system resilience under duress."""

    def __init__(self):
        self.breaker_registry = CircuitBreakerRegistry()
        self.dlq = DeadLetterQueue()
        self.coordinator = SelfHealingCoordinator(
            breaker_registry=self.breaker_registry,
            dlq=self.dlq,
            initial_delay_sec=0.01,
            max_delay_sec=0.1,
        )

    async def inject_fault_and_test_recovery(
        self,
        fault_type: ChaosFaultType,
        target_service: str = "chaos_ollama_endpoint",
    ) -> ChaosSimulationResult:
        """Injects a specific fault into a simulated workload and verifies recovery."""
        start_ts = time.time()
        fallback_invoked = False

        async def failing_operation():
            if fault_type == ChaosFaultType.LATENCY_SPIKE:
                await asyncio.sleep(0.15)
                raise TimeoutError("Injected latency spike: operation timed out")
            elif fault_type == ChaosFaultType.CONNECTION_DROP:
                raise ConnectionResetError("Injected socket disconnect: connection dropped by peer")
            elif fault_type == ChaosFaultType.PROCESS_CRASH:
                raise RuntimeError("Injected process abort: model worker crashed with SIGSEGV")
            elif fault_type == ChaosFaultType.CORRUPTED_PAYLOAD:
                raise ValueError("Injected poison pill: invalid JSON tokens received")

        async def degraded_fallback():
            nonlocal fallback_invoked
            fallback_invoked = True
            return "degraded_mode_cached_response"

        # 1. Execute workload under fault conditions with fallback
        res, ok, err = await self.coordinator.execute_resiliently(
            operation_name=f"{target_service}_{fault_type.value}",
            coro_fn=failing_operation,
            fallback_fn=degraded_fallback,
            max_retries=2,
            circuit_service_name=target_service,
        )

        duration_ms = (time.time() - start_ts) * 1000.0

        # Check circuit state
        breaker = self.breaker_registry.get_or_create(target_service)
        is_open = breaker.state.value == "OPEN"

        # Check DLQ status
        records = self.dlq.list_records(limit=10)
        has_dlq = any(target_service in r.task_id or target_service in r.origin_service for r in records)

        logger.info(
            f"[ChaosInjector] Tested {fault_type.value}: "
            f"Fallback={fallback_invoked}, CircuitOpen={is_open}, Duration={duration_ms:.1f}ms"
        )

        return ChaosSimulationResult(
            fault_type=fault_type,
            circuit_tripped=is_open,
            fallback_activated=fallback_invoked,
            dlq_enqueued=has_dlq,
            total_duration_ms=round(duration_ms, 2),
            recovered=ok and (res == "degraded_mode_cached_response"),
            error_summary=err,
        )


chaos_fault_injector = ChaosFaultInjector()
