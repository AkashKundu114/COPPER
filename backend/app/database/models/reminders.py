from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.postgres import get_db
from app.database.models.reminders import Reminder
from app.ai.agents.reminder_agent import reminder_agent
from app.ai.orchestration.task_scheduler import (
    schedule_once, schedule_recurring, remove_job, list_jobs,
)
from app.core.logger import logger
import asyncio

router = APIRouter(prefix="/reminders", tags=["reminders"])


class ReminderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    due_at: str  # ISO datetime string
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None


class ReminderFromText(BaseModel):
    text: str


def _fire_reminder(reminder_id: int):
    """
    Sync wrapper so APScheduler can call our async broadcast.
    APScheduler >= 3.x does not support async job functions out of the box
    unless AsyncIOScheduler is used AND the event loop is the same one.
    Using asyncio.run_coroutine_threadsafe ensures correctness.
    """
    loop = asyncio.get_event_loop()
    if loop.is_running():
        asyncio.run_coroutine_threadsafe(_notify_reminder(reminder_id), loop)
    else:
        loop.run_until_complete(_notify_reminder(reminder_id))


async def _notify_reminder(reminder_id: int):
    """Called by scheduler when reminder fires."""
    from app.api.websocket.socket_manager import manager
    await manager.broadcast({
        "type": "reminder",
        "reminder_id": reminder_id,
        "title": "Reminder",
        "body": f"Reminder #{reminder_id} triggered",
    })
    logger.info(f"Reminder {reminder_id} fired")


@router.post("/", status_code=201)
async def create_reminder(req: ReminderCreate, db: Session = Depends(get_db)):
    try:
        due_at = datetime.fromisoformat(req.due_at)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid due_at datetime format")

    reminder = Reminder(
        title=req.title,
        description=req.description,
        due_at=due_at,
        is_recurring=req.is_recurring,
        recurrence_rule=req.recurrence_rule,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    # Schedule notification — use the sync wrapper
    job_id = f"reminder_{reminder.id}"
    if req.is_recurring and req.recurrence_rule:
        schedule_recurring(job_id, _fire_reminder, req.recurrence_rule, args=[reminder.id])
    else:
        schedule_once(job_id, _fire_reminder, due_at, args=[reminder.id])

    return reminder.to_dict()


@router.post("/parse")
async def parse_reminder_from_text(req: ReminderFromText):
    """Extract reminder details from natural language."""
    extracted = await reminder_agent.extract_reminder(req.text)
    if not extracted:
        raise HTTPException(status_code=422, detail="Could not extract reminder details")
    return extracted


@router.get("/")
async def list_reminders(
    completed: bool = False,
    db: Session = Depends(get_db),
):
    reminders = (
        db.query(Reminder)
        .filter(Reminder.is_completed == completed)
        .order_by(Reminder.due_at)
        .all()
    )
    return [r.to_dict() for r in reminders]


@router.get("/scheduler/jobs")
async def scheduled_jobs():
    return list_jobs()


@router.get("/{reminder_id}")
async def get_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder.to_dict()


@router.patch("/{reminder_id}/complete")
async def complete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    reminder.is_completed = True
    db.commit()
    remove_job(f"reminder_{reminder_id}")
    return {"completed": True}


@router.delete("/{reminder_id}")
async def delete_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(Reminder).filter(Reminder.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    db.delete(reminder)
    db.commit()
    remove_job(f"reminder_{reminder_id}")
    return {"deleted": True}
