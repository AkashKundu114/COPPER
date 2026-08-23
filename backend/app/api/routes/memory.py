from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.models.history import ChatHistory
from app.database.postgres import get_db

router = APIRouter(prefix="/memory", tags=["memory"])

@router.get("/profile")
async def get_profile(db: Session = Depends(get_db)):
    total = db.query(ChatHistory).count()
    return {
        "facts": [],
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
