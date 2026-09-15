"""
Unit tests for Asynchronous Concurrency, Event Loop Isolation & Inference Priority Queue.
Verifies priority dispatch order, concurrency throttling, backpressure shedding, and lag metrics.
"""

import asyncio
import time
import pytest

from app.core.inference_queue import InferenceQueueManager, PriorityTier


@pytest.mark.asyncio
async def test_inference_queue_priority_ordering():
    # Setup queue with concurrency = 1 to test strict serialized ordering
    iq = InferenceQueueManager(max_concurrent_inferences=1, max_queue_size=10)
    await iq.start()

    execution_order = []

    async def make_task(name: str, delay: float = 0.05):
        async def _run():
            await asyncio.sleep(delay)
            execution_order.append(name)
            return name
        return _run

    try:
        # First task runs immediately to occupy worker 0
        task_occupy = await make_task("occupy", delay=0.08)
        f_occupy = asyncio.create_task(iq.submit("task_0", task_occupy, priority=PriorityTier.NORMAL))
        await asyncio.sleep(0.01)  # Ensure it starts running

        # While worker is busy, submit Background task first, then Critical task
        task_bg = await make_task("background", delay=0.01)
        task_crit = await make_task("critical", delay=0.01)

        f_bg = asyncio.create_task(iq.submit("task_bg", task_bg, priority=PriorityTier.BACKGROUND))
        f_crit = asyncio.create_task(iq.submit("task_crit", task_crit, priority=PriorityTier.CRITICAL))

        await asyncio.gather(f_occupy, f_bg, f_crit)

        # "critical" must execute BEFORE "background", despite background being submitted first!
        assert execution_order == ["occupy", "critical", "background"]
    finally:
        await iq.stop()


@pytest.mark.asyncio
async def test_inference_queue_concurrency_throttling():
    iq = InferenceQueueManager(max_concurrent_inferences=2, max_queue_size=10)
    await iq.start()

    active_counts = []

    async def sample_task():
        active_counts.append(iq.metrics["current_active_workers"])
        await asyncio.sleep(0.05)
        return "done"

    try:
        tasks = [
            iq.submit(f"t_{i}", sample_task, priority=PriorityTier.NORMAL)
            for i in range(5)
        ]
        results = await asyncio.gather(*tasks)
        assert len(results) == 5
        assert all(r == "done" for r in results)
        # Max active workers should never exceed max_concurrency (2)
        assert max(active_counts) <= 2
    finally:
        await iq.stop()


@pytest.mark.asyncio
async def test_inference_queue_backpressure_shedding():
    iq = InferenceQueueManager(max_concurrent_inferences=1, max_queue_size=2)
    # Queue is capacity 2
    # Fill the queue without starting workers
    async def dummy():
        return 1

    # Occupy queue to capacity
    f1 = asyncio.create_task(iq.submit("t1", dummy, priority=PriorityTier.NORMAL))
    f2 = asyncio.create_task(iq.submit("t2", dummy, priority=PriorityTier.NORMAL))
    await asyncio.sleep(0.01)

    # 3rd submission with BACKGROUND priority should be rejected by backpressure
    with pytest.raises(RuntimeError, match="Background task shed under load"):
        await iq.submit("t3", dummy, priority=PriorityTier.BACKGROUND)

    assert iq.metrics["total_rejected"] == 1


@pytest.mark.asyncio
async def test_inference_queue_event_loop_lag_heartbeat():
    iq = InferenceQueueManager(heartbeat_interval_ms=20.0)
    await iq.start()
    try:
        await asyncio.sleep(0.06)
        telemetry = iq.get_telemetry()
        assert "recent_event_loop_lag_ms" in telemetry
        assert "max_event_loop_lag_ms" in telemetry
    finally:
        await iq.stop()
