from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.anomaly_sentinel import sentinel
from app.core.logger import logger
_scheduler: AsyncIOScheduler | None = None

async def _spider_sense_check():
    try:
        alerts = sentinel.run_checks()
        if alerts:
            from app.api.websocket.manager import manager
            for alert in alerts:
                await manager.broadcast_alert(alert)
    except Exception as e:
        logger.error(f'Spider-Sense check failed: {e}')

def start_scheduler():
    global _scheduler
    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(_spider_sense_check, IntervalTrigger(seconds=30), id='spider_sense', name='Spider-Sense Anomaly Sentinel', replace_existing=True)
    try:
        _scheduler.start()
        logger.info('Spider-Sense Anomaly Sentinel started (30s interval)')
    except Exception as e:
        logger.warning(f'Scheduler start deferred: {e}')

def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        logger.info('Spider-Sense Anomaly Sentinel stopped')
        _scheduler = None