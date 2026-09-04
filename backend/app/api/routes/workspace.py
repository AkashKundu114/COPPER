from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models.workspace import WorkspaceItem
from app.database.postgres import get_db

router = APIRouter(prefix="/workspace", tags=["workspace"])
ALLOWED_KINDS = {"task", "project", "event", "meal", "grocery", "memory"}


class WorkspaceItemInput(BaseModel):
    payload: dict[str, Any]


def validate_kind(kind: str) -> None:
    if kind not in ALLOWED_KINDS:
        raise HTTPException(status_code=404, detail="Unknown workspace collection")


@router.get("/{kind}")
def list_items(kind: str, db: Session = Depends(get_db)):
    validate_kind(kind)
    items = db.query(WorkspaceItem).filter(WorkspaceItem.kind == kind).order_by(WorkspaceItem.created_at.desc()).all()
    return [item.to_dict() for item in items]


@router.post("/{kind}", status_code=201)
def create_item(kind: str, body: WorkspaceItemInput, db: Session = Depends(get_db)):
    validate_kind(kind)
    item = WorkspaceItem(kind=kind, payload=body.payload)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item.to_dict()


@router.patch("/{kind}/{item_id}")
def update_item(kind: str, item_id: str, body: WorkspaceItemInput, db: Session = Depends(get_db)):
    validate_kind(kind)
    item = db.query(WorkspaceItem).filter_by(id=item_id, kind=kind).first()
    if not item:
        raise HTTPException(status_code=404, detail="Workspace item not found")
    item.payload = {**(item.payload or {}), **body.payload}
    db.commit()
    db.refresh(item)
    return item.to_dict()


@router.delete("/{kind}/{item_id}", status_code=204)
def delete_item(kind: str, item_id: str, db: Session = Depends(get_db)):
    validate_kind(kind)
    item = db.query(WorkspaceItem).filter_by(id=item_id, kind=kind).first()
    if not item:
        raise HTTPException(status_code=404, detail="Workspace item not found")
    db.delete(item)
    db.commit()
