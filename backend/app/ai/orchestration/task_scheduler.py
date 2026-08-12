import asyncio
from app.core.logger import logger
_scheduler_task = None
_running = False

async def _background_scheduler_loop():
    global _running
    logger.info('COPPER background task scheduler started')
    while _running:
        try:
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f'Error in background task scheduler: {e}')
            await asyncio.sleep(10)

def start_scheduler():
    global _scheduler_task, _running
    _running = True
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            _scheduler_task = loop.create_task(_background_scheduler_loop())
    except Exception as e:
        logger.warning(f'Background task scheduler deferred: {e}')

def stop_scheduler():
    global _scheduler_task, _running
    _running = False
    if _scheduler_task:
        _scheduler_task.cancel()
        logger.info('COPPER background task scheduler stopped')