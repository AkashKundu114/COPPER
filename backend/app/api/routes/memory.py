from datetime import UTC, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.models.history import ChatHistory
from app.database.models.memory_v2 import MemoryStatus, MemoryType, UserMemoryV2
from app.database.postgres import get_db

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: str
    type: Optional[str] = "observation"  # fact, observation, hypothesis
    category: Optional[str] = "General"
    confidence: Optional[float] = 0.95
    evidenceCount: Optional[int] = Field(default=None, alias="evidence_count")
    lastConfirmed: Optional[str] = Field(default=None, alias="last_confirmed")


class MemoryUpdateInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    content: Optional[str] = None
    type: Optional[str] = None
    category: Optional[str] = None
    confidence: Optional[float] = None
    evidenceCount: Optional[int] = Field(default=None, alias="evidence_count")
    status: Optional[str] = None


def serialize_memory(m: UserMemoryV2) -> dict:
    return {
        "id": str(m.id),
        "content": m.content,
        "type": m.type.value if hasattr(m.type, "value") else str(m.type),
        "category": m.category or "General",
        "confidence": m.confidence,
        "evidenceCount": m.evidence_count,
        "evidence_count": m.evidence_count,
        "lastConfirmed": m.last_confirmed_at.strftime("%Y-%m-%d %H:%M") if m.last_confirmed_at else "Recently",
        "last_confirmed_at": m.last_confirmed_at.isoformat() if m.last_confirmed_at else None,
        "status": m.status.value if hasattr(m.status, "value") else str(m.status),
        "created_at": m.created_at.isoformat() if m.created_at else None,
        "updated_at": m.updated_at.isoformat() if m.updated_at else None,
    }


@router.get("")
def list_memories(
    type: Optional[str] = Query(None, description="Filter by memory type"),
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search keyword in content or category"),
    status: Optional[str] = Query("active", description="Filter by status (default active, or 'all')"),
    db: Session = Depends(get_db),
):
    query = db.query(UserMemoryV2)
    if status and status != "all":
        try:
            mem_status = MemoryStatus(status.lower())
            query = query.filter(UserMemoryV2.status == mem_status)
        except ValueError:
            pass

    if type and type != "all":
        try:
            mem_type = MemoryType(type.lower())
            query = query.filter(UserMemoryV2.type == mem_type)
        except ValueError:
            pass

    if category:
        query = query.filter(UserMemoryV2.category.ilike(f"%{category}%"))

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                UserMemoryV2.content.ilike(search_filter),
                UserMemoryV2.category.ilike(search_filter),
            )
        )

    memories = query.order_by(UserMemoryV2.created_at.desc()).all()
    return [serialize_memory(m) for m in memories]


@router.post("", status_code=201)
def create_memory(body: MemoryCreateInput, db: Session = Depends(get_db)):
    if not body.content or not body.content.strip():
        raise HTTPException(status_code=400, detail="Memory content cannot be empty")

    try:
        mem_type = MemoryType(body.type.lower()) if body.type else MemoryType.OBSERVATION
    except ValueError:
        mem_type = MemoryType.OBSERVATION

    conf = max(0.0, min(1.0, float(body.confidence if body.confidence is not None else 0.95)))
    ev_count = max(1, body.evidenceCount if body.evidenceCount is not None else 1)

    memory = UserMemoryV2(
        content=body.content.strip(),
        type=mem_type,
        category=body.category.strip() if body.category else "General",
        confidence=conf,
        evidence_count=ev_count,
        status=MemoryStatus.ACTIVE,
        last_confirmed_at=datetime.now(UTC),
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)
    return serialize_memory(memory)


@router.get("/profile")
async def get_profile(db: Session = Depends(get_db)):
    total = db.query(ChatHistory).count()
    facts = (
        db.query(UserMemoryV2)
        .filter(UserMemoryV2.status == MemoryStatus.ACTIVE, UserMemoryV2.type == MemoryType.FACT)
        .limit(10)
        .all()
    )
    return {
        "facts": [
            {
                "key": f.category or "fact",
                "value": f.content,
                "confidence": f.confidence,
                "observed_n": f.evidence_count,
                "updated_at": f.updated_at.isoformat() if f.updated_at else (f.created_at.isoformat() if f.created_at else ""),
            }
            for f in facts
        ],
        "total_interactions": total,
        "relationship_tier": "Trusted Partner" if total > 20 else "Acquaintance",
        "most_used_agent": "OMNI",
        "agents_met": 3,
        "agents_total": 5,
    }


@router.post("/reset")
async def reset_profile(db: Session = Depends(get_db)):
    db.query(ChatHistory).delete()
    db.commit()
    return {"reset": True}


@router.get("/{memory_id}")
def get_memory(memory_id: str, db: Session = Depends(get_db)):
    try:
        mid = int(memory_id)
        memory = db.query(UserMemoryV2).filter(UserMemoryV2.id == mid).first()
    except ValueError:
        memory = None

    if not memory:
        raise HTTPException(status_code=404, detail="Memory item not found")
    return serialize_memory(memory)


@router.patch("/{memory_id}")
def update_memory(memory_id: str, body: MemoryUpdateInput, db: Session = Depends(get_db)):
    try:
        mid = int(memory_id)
        memory = db.query(UserMemoryV2).filter(UserMemoryV2.id == mid).first()
    except ValueError:
        memory = None

    if not memory:
        raise HTTPException(status_code=404, detail="Memory item not found")

    if body.content is not None:
        memory.content = body.content.strip()
    if body.category is not None:
        memory.category = body.category.strip()
    if body.type is not None:
        try:
            memory.type = MemoryType(body.type.lower())
        except ValueError:
            pass
    if body.confidence is not None:
        memory.confidence = max(0.0, min(1.0, float(body.confidence)))
    if body.evidenceCount is not None:
        memory.evidence_count = max(1, body.evidenceCount)
    if body.status is not None:
        try:
            memory.status = MemoryStatus(body.status.lower())
        except ValueError:
            pass

    memory.last_confirmed_at = datetime.now(UTC)
    db.commit()
    db.refresh(memory)
    return serialize_memory(memory)


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: str, db: Session = Depends(get_db)):
    try:
        mid = int(memory_id)
        memory = db.query(UserMemoryV2).filter(UserMemoryV2.id == mid).first()
    except ValueError:
        memory = None

    if not memory:
        raise HTTPException(status_code=404, detail="Memory item not found")
    db.delete(memory)
    db.commit()
    return None
