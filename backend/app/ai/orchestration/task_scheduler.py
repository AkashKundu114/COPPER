from datetime import datetime
from typing import Callable, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from app.core.logger import logger

scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        logger.info("Task scheduler started")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Task scheduler stopped")


def schedule_once(
    job_id: str,
    func: Callable,
    run_at: datetime,
    args: list = None,
    kwargs: dict = None,
) -> str:
    trigger = DateTrigger(run_date=run_at)
    scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        args=args or [],
        kwargs=kwargs or {},
        replace_existing=True,
        misfire_grace_time=300,
    )
    logger.info(f"Scheduled job {job_id} at {run_at}")
    return job_id


def schedule_recurring(
    job_id: str,
    func: Callable,
    cron_expr: str,
    args: list = None,
    kwargs: dict = None,
) -> str:
    """Schedule a recurring job using cron expression (e.g. '0 9 * * 1-5')."""
    parts = cron_expr.split()
    trigger = CronTrigger(
        minute=parts[0] if len(parts) > 0 else "*",
        hour=parts[1] if len(parts) > 1 else "*",
        day=parts[2] if len(parts) > 2 else "*",
        month=parts[3] if len(parts) > 3 else "*",
        day_of_week=parts[4] if len(parts) > 4 else "*",
    )
    scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        args=args or [],
        kwargs=kwargs or {},
        replace_existing=True,
    )
    logger.info(f"Scheduled recurring job {job_id}: {cron_expr}")
    return job_id


def remove_job(job_id: str) -> bool:
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Removed job {job_id}")
        return True
    except Exception:
        return False


def list_jobs() -> list[dict]:
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        for job in scheduler.get_jobs()
    ]
