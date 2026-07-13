from fastapi import APIRouter, HTTPException

from app.data.agents import AGENTS, TIER_COLORS, TIER_LABELS
from app.memory import db, learner

router = APIRouter(prefix="/api/agents", tags=["agents"])


def _agent_payload(agent_id: str, cfg: dict) -> dict:
    mem = db.get_agent_memory(agent_id) or {"times_invoked": 0, "familiarity_score": 0, "last_active": None, "notes": "[]"}
    score = mem["familiarity_score"]
    return {
        "id": agent_id,
        "name": cfg["name"],
        "tier": cfg["tier"],
        "tier_label": TIER_LABELS[cfg["tier"]],
        "color": TIER_COLORS[cfg["tier"]],
        "domain": cfg["domain"],
        "blurb": cfg["blurb"],
        "times_invoked": mem["times_invoked"],
        "familiarity_score": score,
        "familiarity_tier": learner.agent_tier(score),
        "glow": learner.glow_intensity(score),
        "last_active": mem["last_active"],
    }


@router.get("")
async def list_agents():
    return [_agent_payload(aid, cfg) for aid, cfg in AGENTS.items()]


@router.get("/{agent_id}")
async def get_agent(agent_id: str):
    agent_id = agent_id.upper()
    if agent_id not in AGENTS:
        raise HTTPException(status_code=404, detail="Unknown agent")
    return _agent_payload(agent_id, AGENTS[agent_id])


@router.get("/{agent_id}/history")
async def agent_history(agent_id: str, limit: int = 20):
    agent_id = agent_id.upper()
    if agent_id not in AGENTS and agent_id != "COPPER":
        raise HTTPException(status_code=404, detail="Unknown agent")
    return db.get_agent_history(agent_id, limit=limit)
