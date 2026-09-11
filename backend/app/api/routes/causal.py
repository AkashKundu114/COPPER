from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.ai.knowledge.causal_engine import causal_engine, CausalEvent, CausalLink, CausalChain

router = APIRouter(prefix="/causal", tags=["causal-reasoning"])

class EventCreateReq(BaseModel):
    description: str
    category: str
    source: str
    entities: list[str] | None = None
    metadata: dict | None = None

class LinkCreateReq(BaseModel):
    cause_id: str
    effect_id: str
    relationship: str
    confidence: float
    evidence: str = ""

class WhyReq(BaseModel):
    question: str

@router.post("/events")
async def record_event(req: EventCreateReq):
    event = causal_engine.record_event(
        description=req.description,
        category=req.category,
        source=req.source,
        entities=req.entities,
        metadata=req.metadata,
    )
    return {"status": "success", "event": event}

@router.get("/events")
async def get_events(hours: int = 24, category: str | None = None, limit: int = 100):
    events = causal_engine.get_timeline(hours=hours, category=category)
    return {"status": "success", "events": events[-limit:]}

@router.post("/links")
async def add_causal_link(req: LinkCreateReq):
    link = causal_engine.add_causal_link(
        cause_id=req.cause_id,
        effect_id=req.effect_id,
        relationship=req.relationship,
        confidence=req.confidence,
        evidence=req.evidence,
    )
    return {"status": "success", "link": link}

@router.post("/infer")
async def infer_links():
    links = causal_engine.infer_links()
    return {"status": "success", "inferred_links": len(links), "links": links}

@router.post("/why")
async def ask_why(req: WhyReq):
    chain = await causal_engine.query_why(req.question)
    return {"status": "success", "chain": chain}

@router.get("/events/{event_id}/causes")
async def get_event_causes(event_id: str, depth: int = Query(5)):
    causes = causal_engine.get_event_causes(event_id, depth)
    return {"status": "success", "causes": causes}

@router.get("/events/{event_id}/effects")
async def get_event_effects(event_id: str, depth: int = Query(5)):
    effects = causal_engine.get_event_effects(event_id, depth)
    return {"status": "success", "effects": effects}

@router.get("/stats")
async def get_stats():
    return causal_engine.get_stats()
