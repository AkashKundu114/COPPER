from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from app.ai.ambient.activity_timeline import activity_timeline
from app.ai.ambient.context_watcher import context_watcher

router = APIRouter(prefix="/ambient", tags=["ambient"])


@router.get("/timeline")
async def get_timeline(hours: int = 24):
    return context_watcher.get_timeline(hours)


@router.get("/sessions")
async def get_sessions(hours: int = 24):
    return context_watcher.get_sessions(hours)


@router.get("/stats")
async def get_stats(hours: int = 24) -> Dict[str, Any]:
    return activity_timeline.get_productivity_stats(hours)


@router.get("/current")
async def get_current_context():
    return context_watcher.get_current_context()


@router.get("/summary")
async def get_summary(date: str | None = None) -> Dict[str, str]:
    if date:
        try:
            target_date = datetime.fromisoformat(date)
        except ValueError:
            target_date = datetime.now()
    else:
        target_date = datetime.now()

    summary = activity_timeline.get_daily_summary(target_date)
    return {"summary": summary}
