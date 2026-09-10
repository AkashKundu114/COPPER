from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from app.database.models.project import Project
from app.database.postgres import get_db

router = APIRouter(prefix="/projects", tags=["projects"])


class ProjectCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    health: Optional[str] = "healthy"
    reason: Optional[str] = "Project milestone tracking active."
    completedTasks: Optional[int] = Field(default=None, alias="completed_tasks")
    totalTasks: Optional[int] = Field(default=None, alias="total_tasks")


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    health: Optional[str] = None
    reason: Optional[str] = None
    completedTasks: Optional[int] = Field(default=None, alias="completed_tasks")
    totalTasks: Optional[int] = Field(default=None, alias="total_tasks")


@router.get("")
def list_projects(
    health: Optional[str] = Query(None, description="Filter by project health"),
    db: Session = Depends(get_db),
):
    query = db.query(Project)
    if health and health != "all":
        query = query.filter(Project.health == health)
    projects = query.order_by(Project.created_at.desc()).all()
    return [project.to_dict() for project in projects]


@router.post("", status_code=201)
def create_project(body: ProjectCreate, db: Session = Depends(get_db)):
    if not body.name or not body.name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")

    completed = body.completedTasks if body.completedTasks is not None else 0
    total = max(1, body.totalTasks if body.totalTasks is not None else 1)

    project = Project(
        name=body.name.strip(),
        health=body.health or "healthy",
        reason=body.reason.strip() if body.reason else "Project milestone tracking active.",
        completed_tasks=completed,
        total_tasks=total,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project.to_dict()


@router.patch("/{project_id}")
def update_project(project_id: str, body: ProjectUpdate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if body.name is not None:
        project.name = body.name.strip()
    if body.health is not None:
        project.health = body.health
    if body.reason is not None:
        project.reason = body.reason.strip()
    if body.completedTasks is not None:
        project.completed_tasks = max(0, body.completedTasks)
    if body.totalTasks is not None:
        project.total_tasks = max(1, body.totalTasks)

    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.put("/{project_id}")
def replace_project(project_id: str, body: ProjectCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project.name = body.name.strip()
    project.health = body.health or "healthy"
    project.reason = body.reason.strip() if body.reason else "Project milestone tracking active."
    project.completed_tasks = body.completedTasks if body.completedTasks is not None else 0
    project.total_tasks = max(1, body.totalTasks if body.totalTasks is not None else 1)

    db.commit()
    db.refresh(project)
    return project.to_dict()


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: str, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return None
