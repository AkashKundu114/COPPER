from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models.task import Task
from app.database.postgres import get_db

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    project: Optional[str] = "General"
    priority: Optional[str] = "medium"
    duration: Optional[str] = "30m"
    status: Optional[str] = "inbox"


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    project: Optional[str] = None
    priority: Optional[str] = None
    duration: Optional[str] = None
    status: Optional[str] = None


@router.get("")
def list_tasks(
    status: Optional[str] = Query(None, description="Filter by task status"),
    project: Optional[str] = Query(None, description="Filter by project name"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    db: Session = Depends(get_db),
):
    query = db.query(Task)
    if status and status != "all":
        query = query.filter(Task.status == status)
    if project:
        query = query.filter(Task.project == project)
    if priority:
        query = query.filter(Task.priority == priority)
    tasks = query.order_by(Task.created_at.desc()).all()
    return [task.to_dict() for task in tasks]


@router.post("", status_code=201)
def create_task(body: TaskCreate, db: Session = Depends(get_db)):
    if not body.title or not body.title.strip():
        raise HTTPException(status_code=400, detail="Task title is required")
    task = Task(
        title=body.title.strip(),
        project=body.project.strip() if body.project else "General",
        priority=body.priority or "medium",
        duration=body.duration.strip() if body.duration else "30m",
        status=body.status or "inbox",
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task.to_dict()


@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task.to_dict()


@router.patch("/{task_id}")
def update_task(task_id: str, body: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.title is not None:
        task.title = body.title.strip()
    if body.project is not None:
        task.project = body.project.strip()
    if body.priority is not None:
        task.priority = body.priority
    if body.duration is not None:
        task.duration = body.duration.strip()
    if body.status is not None:
        task.status = body.status

    db.commit()
    db.refresh(task)
    return task.to_dict()


@router.put("/{task_id}")
def replace_task(task_id: str, body: TaskCreate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.title = body.title.strip()
    task.project = body.project.strip() if body.project else "General"
    task.priority = body.priority or "medium"
    task.duration = body.duration.strip() if body.duration else "30m"
    task.status = body.status or "inbox"

    db.commit()
    db.refresh(task)
    return task.to_dict()


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return None
