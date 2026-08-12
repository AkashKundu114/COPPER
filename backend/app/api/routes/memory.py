from fastapi import APIRouter
from app.memory import db, learner
from app.data.agents import AGENTS
router = APIRouter(prefix='/memory', tags=['memory'])

@router.get('/profile')
async def get_profile():
    total = db.total_interactions()
    agent_mem = db.get_all_agent_memory()
    most_used = max(agent_mem.items(), key=lambda kv: kv[1]['times_invoked'], default=(None, None))
    return {'facts': db.get_profile(), 'total_interactions': total, 'relationship_tier': learner.relationship_tier(total), 'most_used_agent': most_used[0], 'agents_met': len(agent_mem), 'agents_total': len(AGENTS)}

@router.post('/reset')
async def reset_profile():
    db.reset_profile()
    return {'reset': True}