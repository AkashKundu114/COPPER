from dataclasses import asdict
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.ai.memory.provenance import provenance_tracker

router = APIRouter(prefix="/provenance", tags=["memory-provenance"])


class FactCreate(BaseModel):
    fact: str
    source_type: str
    source_id: str
    confidence: Optional[float] = 0.8
    tags: Optional[List[str]] = None


class ConfirmInput(BaseModel):
    source_id: str
    confidence: Optional[float] = 0.9


class ContradictInput(BaseModel):
    source_id: str
    counter_evidence: str
    confidence: Optional[float] = 0.7


class ReviseInput(BaseModel):
    new_fact: str
    reason: str
    source_id: str


@router.post("/facts", status_code=201)
def record_fact(body: FactCreate):
    record = provenance_tracker.record_fact(
        fact=body.fact,
        source_type=body.source_type,
        source_id=body.source_id,
        confidence=body.confidence,
        tags=body.tags,
    )
    return asdict(record)


@router.get("/facts")
def search_facts(
    q: str = Query("", description="Search query"),
    min_confidence: float = Query(0.0, description="Minimum confidence score"),
    status: str = Query("active", description="Filter by status (or 'all')"),
    limit: int = Query(50, description="Max results"),
):
    results = provenance_tracker.search_facts(q, min_confidence)
    if status != "all":
        results = [r for r in results if r.status == status]
    return [asdict(r) for r in results[:limit]]


@router.get("/facts/{record_id}")
def get_provenance(record_id: str):
    record = provenance_tracker.get_provenance(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return asdict(record)


@router.post("/facts/{record_id}/confirm")
def confirm_fact(record_id: str, body: ConfirmInput):
    record = provenance_tracker.get_provenance(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    provenance_tracker.confirm_fact(record.fact_hash, body.source_id, body.confidence)
    return asdict(provenance_tracker.get_provenance(record_id))


@router.post("/facts/{record_id}/contradict")
def contradict_fact(record_id: str, body: ContradictInput):
    record = provenance_tracker.get_provenance(record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    provenance_tracker.contradict_fact(
        record.fact_hash, body.source_id, body.counter_evidence, body.confidence
    )
    return asdict(provenance_tracker.get_provenance(record_id))


@router.post("/facts/{record_id}/revise")
def revise_fact(record_id: str, body: ReviseInput):
    new_record = provenance_tracker.revise_fact(record_id, body.new_fact, body.reason, body.source_id)
    if not new_record:
        raise HTTPException(status_code=404, detail="Record not found")
    return asdict(new_record)


@router.get("/explain")
def explain_belief(fact: str = Query(..., description="The fact to explain")):
    result = provenance_tracker.explain_belief(fact)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/uncertain")
def get_uncertain_facts():
    results = provenance_tracker.get_uncertain_facts()
    return [asdict(r) for r in results]


@router.get("/stats")
def get_stats():
    return provenance_tracker.get_stats()
