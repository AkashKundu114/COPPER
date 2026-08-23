import pytest
from app.ai.orchestration.task_scheduler import (
    APSCHEDULER_AVAILABLE,
    _spider_sense_check,
    start_scheduler,
    stop_scheduler,
)


def test_scheduler_lifecycle():
    start_scheduler()
    stop_scheduler()


def test_scheduler_double_stop():
    stop_scheduler()
    stop_scheduler()


@pytest.mark.asyncio
async def test_spider_sense_check_execution():
    await _spider_sense_check()


def test_scheduler_availability_flag():
    assert isinstance(APSCHEDULER_AVAILABLE, bool)
