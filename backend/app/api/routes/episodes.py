from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.database.postgres import get_db
from app.database.models.episode import EpisodeOutcome
from app.services.episode_service import episode_service
router = APIRouter(prefix='/episodes', tags=['episodes'])

class EpisodeCreateRequest(BaseModel):
    context: str
    project: Optional[str] = None
    task: Optional[str] = None
    goal: Optional[str] = None
    problem: Optional[str] = None
    decision: Optional[str] = None
    outcome: Optional[EpisodeOutcome] = None
    confidence: float = 0.5
    tags: Optional[list[str]] = None

@router.get('/')
async def list_episodes(context: Optional[str] = None, limit: int = 20, db: Session = Depends(get_db)):
    episodes = episode_service.get_recent_episodes(db, limit=limit, context=context)
    return [ep.to_dict() for ep in episodes]

@router.get('/similar')
async def find_similar(query: str, limit: int = 5):
    results = await episode_service.find_similar_episodes(query, limit=limit)
    return results

@router.get('/{episode_id}')
async def get_episode(episode_id: int, db: Session = Depends(get_db)):
    ep = episode_service.get_episode_by_id(db, episode_id)
    if not ep:
        raise HTTPException(status_code=404, detail='Episode not found')
    return ep.to_dict()

@router.post('/')
async def create_episode(req: EpisodeCreateRequest, db: Session = Depends(get_db)):
    ep = await episode_service.record_episode(db, context=req.context, project=req.project, task=req.task, goal=req.goal, problem=req.problem, decision=req.decision, outcome=req.outcome, confidence=req.confidence, tags=req.tags)
    return ep.to_dict()
