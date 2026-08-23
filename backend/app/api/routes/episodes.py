from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database.models.episode import EpisodeOutcome
from app.database.postgres import get_db
from app.services.episode_service import episode_service

router = APIRouter(prefix="/episodes", tags=["episodes"])


class EpisodeCreateRequest(BaseModel):
    context: str
    project: str | None = None
    task: str | None = None
    goal: str | None = None
    problem: str | None = None
    decision: str | None = None
    outcome: EpisodeOutcome | None = None
    confidence: float = 0.5
    tags: list[str] | None = None


@router.get("/")
async def list_episodes(context: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    episodes = episode_service.get_recent_episodes(db, limit=limit, context=context)
    return [ep.to_dict() for ep in episodes]


@router.get("/similar")
async def find_similar(query: str, limit: int = 5):
    results = await episode_service.find_similar_episodes(query, limit=limit)
    return results


@router.get("/{episode_id}")
async def get_episode(episode_id: int, db: Session = Depends(get_db)):
    ep = episode_service.get_episode_by_id(db, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    return ep.to_dict()


@router.post("/")
async def create_episode(req: EpisodeCreateRequest, db: Session = Depends(get_db)):
    ep = await episode_service.record_episode(
        db,
        context=req.context,
        project=req.project,
        task=req.task,
        goal=req.goal,
        problem=req.problem,
        decision=req.decision,
        outcome=req.outcome,
        confidence=req.confidence,
        tags=req.tags,
    )
    return ep.to_dict()
