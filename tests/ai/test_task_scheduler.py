import pytest
from app.ai.orchestration.task_scheduler import (
    start_scheduler,
    stop_scheduler,
    _spider_sense_check,
    APSCHEDULER_AVAILABLE
)


def test_scheduler_lifecycle():
    # Calling start and stop should be safe and idempotent
    start_scheduler()
    stop_scheduler()


def test_scheduler_double_stop():
    stop_scheduler()
    stop_scheduler()


@pytest.mark.asyncio
async def test_spider_sense_check_execution():
    # Calling internal background check function should execute without raising unhandled exceptions
    await _spider_sense_check()


def test_scheduler_availability_flag():
    assert isinstance(APSCHEDULER_AVAILABLE, bool)
