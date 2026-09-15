"""
Asynchronous Concurrency, Event Loop Isolation & Inference Priority Queue.

Backend & Systems Architecture Concept:
Decoupling the FastAPI async I/O network control plane from compute-heavy
CPU/GPU inference tasks to eliminate Event Loop Starvation and P99 latency spikes.

Architecture:
1. Priority-Tiered Bounded Queue (asyncio.PriorityQueue):
   - CRITICAL (0): Interactive User Voice, Wake-word, and Direct Chat.
   - HIGH (1): Fast-path Intent Routing & Guardian Security Checks.
   - NORMAL (2): Multi-Agent DAG Sub-tasks.
   - BACKGROUND (3): Reflection cycle, Memory Decay, and Telemetry sweeps.
2. Leaky-Bucket Backpressure:
   - Gracefully sheds or defers background tasks when queue depth exceeds capacity.
3. Event Loop Lag Heartbeat:
   - Measures event loop scheduling delay in milliseconds. Alerts on blocking tasks.
4. Concurrency Limiter:
   - Strict semaphore bounds (default: 2 heavy concurrent inferences) to avoid GPU thrashing.
"""

import asyncio
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any

from app.core.logger import logger


class PriorityTier(IntEnum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    BACKGROUND = 3


@dataclass(order=True)
class QueuedInferenceTask:
    priority: int
    task_id: str = field(compare=False)
    timestamp: float = field(compare=False, default_factory=time.time)
    coro_fn: Any = field(compare=False, default=None)
    future: asyncio.Future = field(compare=False, default_factory=asyncio.Future)


class InferenceQueueManager:
    """
    Manages priority dispatching, concurrency throttling, and event loop health.
    """

    def __init__(
        self,
        max_concurrent_inferences: int = 2,
        max_queue_size: int = 128,
        heartbeat_interval_ms: float = 50.0,
    ):
        self.max_concurrency = max_concurrent_inferences
        self.max_queue_size = max_queue_size
        self.heartbeat_interval_s = heartbeat_interval_ms / 1000.0

        self._queue: asyncio.PriorityQueue[QueuedInferenceTask] = asyncio.PriorityQueue(maxsize=max_queue_size)
        self._semaphore = asyncio.Semaphore(max_concurrent_inferences)
        self._workers: list[asyncio.Task] = []
        self._heartbeat_task: asyncio.Task | None = None

        # Telemetry metrics
        self.metrics = {
            "total_enqueued": 0,
            "total_processed": 0,
            "total_rejected": 0,
            "current_active_workers": 0,
            "max_event_loop_lag_ms": 0.0,
            "recent_event_loop_lag_ms": 0.0,
            "event_loop_lag_spikes": 0,
        }
        self._running = False

    async def start(self) -> None:
        """Starts worker pool and event loop lag monitor."""
        if self._running:
            return
        self._running = True

        # Launch worker pool
        for i in range(self.max_concurrency):
            t = asyncio.create_task(self._worker_loop(i), name=f"inference_worker_{i}")
            self._workers.append(t)

        # Launch event loop lag monitor
        self._heartbeat_task = asyncio.create_task(self._lag_heartbeat_loop(), name="event_loop_heartbeat")
        logger.info(f"[InferenceQueue] Started with {self.max_concurrency} worker slots.")

    async def stop(self) -> None:
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        for w in self._workers:
            w.cancel()
        self._workers.clear()

    async def submit(
        self,
        task_id: str,
        coro_fn: Callable[[], Coroutine[Any, Any, Any]],
        priority: PriorityTier = PriorityTier.NORMAL,
    ) -> Any:
        """
        Submits an inference coroutine to the priority queue with backpressure.
        Returns the result once processed.
        """
        # Backpressure check: if queue is full and priority is BACKGROUND, shed load immediately
        if self._queue.qsize() >= self.max_queue_size:
            if priority == PriorityTier.BACKGROUND:
                self.metrics["total_rejected"] += 1
                raise RuntimeError("InferenceQueue saturated: Background task shed under load.")
            # For critical/high, wait or raise
            if self._queue.full():
                self.metrics["total_rejected"] += 1
                raise RuntimeError("InferenceQueue saturated: Queue full.")

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        task = QueuedInferenceTask(
            priority=int(priority),
            task_id=task_id,
            coro_fn=coro_fn,
            future=future,
        )

        await self._queue.put(task)
        self.metrics["total_enqueued"] += 1

        # Await completion
        return await future

    async def _worker_loop(self, worker_id: int) -> None:
        while self._running:
            try:
                task = await self._queue.get()
                async with self._semaphore:
                    self.metrics["current_active_workers"] += 1
                    try:
                        res = await task.coro_fn()
                        if not task.future.done():
                            task.future.set_result(res)
                    except Exception as exc:
                        if not task.future.done():
                            task.future.set_exception(exc)
                    finally:
                        self.metrics["current_active_workers"] -= 1
                        self.metrics["total_processed"] += 1
                        self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[InferenceQueue] Worker {worker_id} exception: {e}")

    async def _lag_heartbeat_loop(self) -> None:
        """
        Calculates Event Loop Lag (ms):
        Sleeps for heartbeat_interval_s. The actual wall-clock elapsed time minus
        the expected time indicates how long synchronous work blocked the event loop.
        """
        while self._running:
            t0 = time.perf_counter()
            try:
                await asyncio.sleep(self.heartbeat_interval_s)
                t1 = time.perf_counter()
                elapsed_ms = (t1 - t0) * 1000.0
                lag_ms = max(0.0, elapsed_ms - (self.heartbeat_interval_s * 1000.0))

                self.metrics["recent_event_loop_lag_ms"] = round(lag_ms, 2)
                if lag_ms > self.metrics["max_event_loop_lag_ms"]:
                    self.metrics["max_event_loop_lag_ms"] = round(lag_ms, 2)

                # Lag > 50ms indicates significant event loop starvation
                if lag_ms > 50.0:
                    self.metrics["event_loop_lag_spikes"] += 1
                    logger.warning(f"[EventLoopMonitor] High event loop lag detected: {lag_ms:.2f}ms")
            except asyncio.CancelledError:
                break

    def get_telemetry(self) -> dict[str, Any]:
        return {
            "queue_depth": self._queue.qsize(),
            "max_queue_capacity": self.max_queue_size,
            "max_concurrency_slots": self.max_concurrency,
            **self.metrics,
        }


inference_queue = InferenceQueueManager()
