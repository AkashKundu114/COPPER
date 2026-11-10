"""Multi-Client Concurrency & Distributed Lock Stress Coordinator for C.O.P.P.E.R.

Simulates high-concurrency workloads across distributed session stores and tests
lock lease contention under race-condition pressure to verify mutual exclusion,
zero state corruption, and throughput stability.
"""

from __future__ import annotations

import asyncio
import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger
from app.core.scalability.distributed_lock import DistributedLockManager, distributed_lock_manager
from app.core.scalability.session_store import SharedSessionStore, shared_session_store


@dataclass
class LockContentionMetric:
    task_id: str
    acquired: bool
    acquisition_time_ms: float
    hold_duration_ms: float
    error: str | None = None


@dataclass
class ScalabilityStressReport:
    stress_run_id: str
    timestamp: float
    concurrency_level: int
    session_writes_total: int
    session_writes_successful: int
    lock_attempts_total: int
    mutual_exclusion_preserved: bool
    active_conflicts_detected: int
    avg_lock_acquisition_ms: float
    report_passed: bool
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ScalabilityStressCoordinator:
    """Orchestrates high-concurrency stress verification for locks and session stores."""

    def __init__(
        self,
        lock_mgr: DistributedLockManager | None = None,
        session_store: SharedSessionStore | None = None,
    ):
        self.lock_mgr = lock_mgr or distributed_lock_manager
        self.session_store = session_store or shared_session_store

    async def stress_test_concurrent_sessions(
        self,
        num_sessions: int = 10,
        messages_per_session: int = 5,
    ) -> tuple[int, int]:
        """Stress-tests multi-replica concurrent writes to distinct session streams."""
        tasks = []

        async def worker(session_id: str):
            successes = 0
            for i in range(messages_per_session):
                res = await self.session_store.append_message(
                    session_id=session_id,
                    role="user" if i % 2 == 0 else "assistant",
                    content=f"Stress test message payload sequence {i}",
                )
                if res and "content" in res:
                    successes += 1
            return successes

        for s_idx in range(num_sessions):
            session_id = f"stress-session-{s_idx}"
            tasks.append(worker(session_id))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        total_writes = num_sessions * messages_per_session
        successful_writes = sum(r for r in results if isinstance(r, int))
        return total_writes, successful_writes

    async def stress_test_lock_contention(
        self,
        shared_resource: str = "critical_ledger_resource",
        concurrency: int = 10,
    ) -> tuple[bool, int, list[LockContentionMetric]]:
        """Stress-tests mutual exclusion under concurrent lock competition."""
        concurrent_holders = 0
        max_concurrent_detected = 0
        metrics: list[LockContentionMetric] = []
        lock_state_lock = asyncio.Lock()

        async def lock_worker(worker_id: str):
            nonlocal concurrent_holders, max_concurrent_detected
            t0 = time.perf_counter()
            acquired_lock = await self.lock_mgr.acquire_lock(
                resource=shared_resource,
                lease_seconds=5,
                acquire_timeout=3.0,
            )

            acq_time = (time.perf_counter() - t0) * 1000.0

            if not acquired_lock:
                metrics.append(
                    LockContentionMetric(
                        task_id=worker_id,
                        acquired=False,
                        acquisition_time_ms=round(acq_time, 2),
                        hold_duration_ms=0.0,
                        error="Lock acquisition timed out",
                    )
                )
                return

            # Entered critical section
            async with lock_state_lock:
                concurrent_holders += 1
                if concurrent_holders > max_concurrent_detected:
                    max_concurrent_detected = concurrent_holders

            # Simulate critical section work
            hold_start = time.perf_counter()
            await asyncio.sleep(0.01)
            hold_duration = (time.perf_counter() - hold_start) * 1000.0

            # Exit critical section
            async with lock_state_lock:
                concurrent_holders -= 1

            await acquired_lock.release()

            metrics.append(
                LockContentionMetric(
                    task_id=worker_id,
                    acquired=True,
                    acquisition_time_ms=round(acq_time, 2),
                    hold_duration_ms=round(hold_duration, 2),
                )
            )

        tasks = [lock_worker(f"worker-{i}") for i in range(concurrency)]
        await asyncio.gather(*tasks, return_exceptions=True)

        mutual_exclusion_preserved = (max_concurrent_detected <= 1)
        return mutual_exclusion_preserved, max_concurrent_detected, metrics

    async def run_full_stress_suite(
        self,
        concurrency: int = 10,
    ) -> ScalabilityStressReport:
        """Executes session concurrency and lock contention stress tests."""
        # 1. Concurrent Sessions
        tot_writes, succ_writes = await self.stress_test_concurrent_sessions(
            num_sessions=concurrency,
            messages_per_session=4,
        )

        # 2. Lock Contention
        mutex_ok, max_holders, metrics = await self.stress_test_lock_contention(
            shared_resource="shared_finops_resource",
            concurrency=concurrency,
        )

        acq_times = [m.acquisition_time_ms for m in metrics if m.acquired]
        avg_acq = (sum(acq_times) / len(acq_times)) if acq_times else 0.0

        ts = time.time()
        stress_id = f"STRESS-{hashlib.sha256(str(ts).encode()).hexdigest()[:12].upper()}"
        report_passed = mutex_ok and (succ_writes == tot_writes)
        signature = hashlib.sha256(f"{stress_id}:{mutex_ok}:{succ_writes}".encode()).hexdigest()

        report = ScalabilityStressReport(
            stress_run_id=stress_id,
            timestamp=ts,
            concurrency_level=concurrency,
            session_writes_total=tot_writes,
            session_writes_successful=succ_writes,
            lock_attempts_total=len(metrics),
            mutual_exclusion_preserved=mutex_ok,
            active_conflicts_detected=max(0, max_holders - 1),
            avg_lock_acquisition_ms=round(avg_acq, 2),
            report_passed=report_passed,
            signature=signature,
        )

        logger.info(
            f"[ScalabilityStressCoordinator] Completed stress suite: Mutex preserved={mutex_ok}, "
            f"Writes={succ_writes}/{tot_writes}, Passed={report_passed}"
        )
        return report


scalability_stress_coordinator = ScalabilityStressCoordinator()
