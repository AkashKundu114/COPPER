import asyncio
import pytest

from app.core.inference_queue import (
    InferenceQueueManager,
    PriorityTier,
)


@pytest.mark.asyncio
async def test_inference_queue_prioritization():
    """Verify high-priority tasks execute before normal-priority tasks in backlog."""
    iq = InferenceQueueManager(max_concurrent_inferences=1, max_queue_size=10)
    await iq.start()
    execution_order = []

    async def slow_first():
        await asyncio.sleep(0.05)
        execution_order.append("first")
        return "first_done"

    async def normal_task():
        execution_order.append("normal")
        return "normal_done"

    async def critical_task():
        execution_order.append("critical")
        return "critical_done"

    # Start first task to occupy the worker
    t1 = asyncio.create_task(iq.submit("t1", slow_first, priority=PriorityTier.NORMAL))
    await asyncio.sleep(0.01)

    # Queue normal, then critical while worker is busy
    t_normal = asyncio.create_task(iq.submit("t_norm", normal_task, priority=PriorityTier.NORMAL))
    t_crit = asyncio.create_task(iq.submit("t_crit", critical_task, priority=PriorityTier.CRITICAL))

    await asyncio.gather(t1, t_normal, t_crit)
    await iq.stop()

    assert execution_order[0] == "first"
    assert execution_order[1] == "critical"  # Critical priority leaped over normal
    assert execution_order[2] == "normal"


@pytest.mark.asyncio
async def test_inference_queue_timeout_and_fallback():
    """Verify task timing out invokes fallback coroutine without raising exception."""
    iq = InferenceQueueManager(max_concurrent_inferences=1)
    await iq.start()

    async def hanging_model():
        await asyncio.sleep(0.5)
        return "unreachable"

    async def fallback_model():
        return "fallback_response_gatekeeper"

    result = await iq.submit(
        task_id="timeout_test",
        coro_fn=hanging_model,
        timeout_s=0.05,
        fallback_fn=fallback_model,
    )
    await iq.stop()

    assert result == "fallback_response_gatekeeper"
    assert iq.metrics["total_timeouts"] == 1
    assert iq.metrics["total_fallbacks_invoked"] == 1
