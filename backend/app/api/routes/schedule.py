from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models.schedule_event import ScheduleEvent
from app.database.postgres import get_db

router = APIRouter(prefix="/schedule", tags=["schedule"])
events_router = APIRouter(prefix="/events", tags=["events"])


class ScheduleEventCreate(BaseModel):
    time: str
    title: str
    category: Optional[str] = "Focus"
    completed: Optional[bool] = False
    date: Optional[str] = None


class ScheduleEventUpdate(BaseModel):
    time: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    completed: Optional[bool] = None
    date: Optional[str] = None


def _list_events(
    category: Optional[str],
    completed: Optional[bool],
    date: Optional[str],
    db: Session,
):
    query = db.query(ScheduleEvent)
    if category and category != "all":
        query = query.filter(ScheduleEvent.category == category)
    if completed is not None:
        query = query.filter(ScheduleEvent.completed == completed)
    if date:
        query = query.filter(ScheduleEvent.date == date)
    events = query.order_by(ScheduleEvent.created_at.asc()).all()
    return [event.to_dict() for event in events]


def _create_event(body: ScheduleEventCreate, db: Session):
    if not body.title or not body.title.strip():
        raise HTTPException(status_code=400, detail="Event title is required")
    if not body.time or not body.time.strip():
        raise HTTPException(status_code=400, detail="Event time is required")

    event = ScheduleEvent(
        time=body.time.strip(),
        title=body.title.strip(),
        category=body.category.strip() if body.category else "Focus",
        completed=bool(body.completed),
        date=body.date.strip() if body.date else None,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event.to_dict()


def _get_event(event_id: str, db: Session):
    event = db.query(ScheduleEvent).filter(ScheduleEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Schedule event not found")
    return event.to_dict()


def _update_event(event_id: str, body: ScheduleEventUpdate, db: Session):
    event = db.query(ScheduleEvent).filter(ScheduleEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Schedule event not found")

    if body.time is not None:
        event.time = body.time.strip()
    if body.title is not None:
        event.title = body.title.strip()
    if body.category is not None:
        event.category = body.category.strip()
    if body.completed is not None:
        event.completed = body.completed
    if body.date is not None:
        event.date = body.date.strip() if body.date else None

    db.commit()
    db.refresh(event)
    return event.to_dict()


def _delete_event(event_id: str, db: Session):
    event = db.query(ScheduleEvent).filter(ScheduleEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Schedule event not found")
    db.delete(event)
    db.commit()
    return None


@router.get("/events")
def list_schedule_events(
    category: Optional[str] = Query(None, description="Filter by event category"),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    date: Optional[str] = Query(None, description="Filter by event date"),
    db: Session = Depends(get_db),
):
    return _list_events(category, completed, date, db)


@router.post("/events", status_code=201)
def create_schedule_event(body: ScheduleEventCreate, db: Session = Depends(get_db)):
    return _create_event(body, db)


@router.get("/events/{event_id}")
def get_schedule_event(event_id: str, db: Session = Depends(get_db)):
    return _get_event(event_id, db)


@router.patch("/events/{event_id}")
def update_schedule_event(event_id: str, body: ScheduleEventUpdate, db: Session = Depends(get_db)):
    return _update_event(event_id, body, db)


@router.delete("/events/{event_id}", status_code=204)
def delete_schedule_event(event_id: str, db: Session = Depends(get_db)):
    return _delete_event(event_id, db)


# Also provide the same endpoints under /events for direct access
@events_router.get("")
def list_events_direct(
    category: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    date: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return _list_events(category, completed, date, db)


@events_router.post("", status_code=201)
def create_event_direct(body: ScheduleEventCreate, db: Session = Depends(get_db)):
    return _create_event(body, db)


@events_router.get("/{event_id}")
def get_event_direct(event_id: str, db: Session = Depends(get_db)):
    return _get_event(event_id, db)


@events_router.patch("/{event_id}")
def update_event_direct(event_id: str, body: ScheduleEventUpdate, db: Session = Depends(get_db)):
    return _update_event(event_id, body, db)


@events_router.delete("/{event_id}", status_code=204)
def delete_event_direct(event_id: str, db: Session = Depends(get_db)):
    return _delete_event(event_id, db)
