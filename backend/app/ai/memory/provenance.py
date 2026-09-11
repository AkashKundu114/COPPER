import json
import hashlib
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, UTC
from pathlib import Path
from typing import Optional

from app.core.logger import logger

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
PROVENANCE_FILE = DATA_DIR / "memory_provenance.json"


@dataclass
class ProvenanceRecord:
    record_id: str
    fact: str
    fact_hash: str
    source_type: str
    source_id: str
    created_at: str
    confidence: float
    current_confidence: float
    revision_history: list[dict] = field(default_factory=list)
    confirmations: int = 0
    contradictions: int = 0
    last_accessed: str | None = None
    access_count: int = 0
    tags: list[str] = field(default_factory=list)
    status: str = "active"

    @classmethod
    def create(cls, fact: str, source_type: str, source_id: str, confidence: float, tags: list[str] = None):
        fact_hash = hashlib.sha256(fact.strip().lower().encode("utf-8")).hexdigest()
        now = datetime.now(UTC).isoformat()
        return cls(
            record_id=str(uuid.uuid4()),
            fact=fact.strip(),
            fact_hash=fact_hash,
            source_type=source_type,
            source_id=source_id,
            created_at=now,
            confidence=confidence,
            current_confidence=confidence,
            last_accessed=now,
            tags=tags or []
        )


class ProvenanceTracker:
    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, ProvenanceRecord] = {}
        self.hash_index: dict[str, str] = {}
        self._load()

    def _load(self):
        if not PROVENANCE_FILE.exists():
            return
        try:
            with open(PROVENANCE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    record = ProvenanceRecord(**item)
                    self.records[record.record_id] = record
                    self.hash_index[record.fact_hash] = record.record_id
        except Exception as e:
            logger.error(f"Error loading provenance data: {e}")

    def _save(self):
        try:
            with open(PROVENANCE_FILE, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in self.records.values()], f, indent=2)
        except Exception as e:
            logger.error(f"Error saving provenance data: {e}")

    def _mark_accessed(self, record: ProvenanceRecord):
        record.last_accessed = datetime.now(UTC).isoformat()
        record.access_count += 1
        self._save()

    def record_fact(
        self, fact: str, source_type: str, source_id: str, confidence: float = 0.8, tags: list[str] = None
    ) -> ProvenanceRecord:
        fact_hash = hashlib.sha256(fact.strip().lower().encode("utf-8")).hexdigest()
        
        if fact_hash in self.hash_index:
            record_id = self.hash_index[fact_hash]
            self.confirm_fact(fact_hash, source_id, confidence)
            return self.records[record_id]

        record = ProvenanceRecord.create(fact, source_type, source_id, confidence, tags)
        self.records[record.record_id] = record
        self.hash_index[record.fact_hash] = record.record_id
        self._save()
        logger.info(f"Recorded new fact provenance: {fact} (id={record.record_id})")
        return record

    def confirm_fact(self, fact_hash: str, source_id: str, confidence: float = 0.9):
        record_id = self.hash_index.get(fact_hash)
        if not record_id:
            return
        
        record = self.records[record_id]
        old_conf = record.current_confidence
        new_conf = 1.0 - (1.0 - old_conf) * (1.0 - confidence)
        
        record.revision_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "confirm",
            "old_confidence": old_conf,
            "new_confidence": new_conf,
            "reason": "Confirmed by another source",
            "source_id": source_id
        })
        
        record.current_confidence = new_conf
        record.confirmations += 1
        record.status = "active"
        self._mark_accessed(record)
        logger.info(f"Confirmed fact {record_id}, conf {old_conf:.2f}->{new_conf:.2f}")

    def contradict_fact(self, fact_hash: str, source_id: str, counter_evidence: str, confidence: float = 0.7):
        record_id = self.hash_index.get(fact_hash)
        if not record_id:
            return

        record = self.records[record_id]
        old_conf = record.current_confidence
        
        # Bayesian downgrade approximation
        new_conf = old_conf * (1.0 - confidence)
        
        record.revision_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "contradict",
            "old_confidence": old_conf,
            "new_confidence": new_conf,
            "reason": counter_evidence,
            "source_id": source_id
        })
        
        record.current_confidence = new_conf
        record.contradictions += 1
        
        if new_conf < 0.1:
            record.status = "retracted"
        elif new_conf < 0.3:
            record.status = "uncertain"
            
        self._mark_accessed(record)
        logger.info(f"Contradicted fact {record_id}, conf {old_conf:.2f}->{new_conf:.2f}")

    def revise_fact(self, record_id: str, new_fact: str, reason: str, source_id: str) -> Optional[ProvenanceRecord]:
        if record_id not in self.records:
            return None
            
        old_record = self.records[record_id]
        old_record.status = "superseded"
        old_record.revision_history.append({
            "timestamp": datetime.now(UTC).isoformat(),
            "action": "superseded",
            "old_confidence": old_record.current_confidence,
            "new_confidence": 0.0,
            "reason": reason,
            "source_id": source_id
        })
        
        new_record = self.record_fact(
            new_fact, old_record.source_type, source_id, old_record.current_confidence, old_record.tags
        )
        self._save()
        logger.info(f"Revised fact {record_id} to new fact {new_record.record_id}")
        return new_record

    def get_provenance(self, record_id: str) -> Optional[ProvenanceRecord]:
        record = self.records.get(record_id)
        if record:
            self._mark_accessed(record)
        return record

    def explain_belief(self, fact: str) -> dict:
        fact_hash = hashlib.sha256(fact.strip().lower().encode("utf-8")).hexdigest()
        record_id = self.hash_index.get(fact_hash)
        
        if not record_id:
            # Try partial match
            matches = [r for r in self.records.values() if fact.lower() in r.fact.lower()]
            if not matches:
                return {"error": "Fact not found"}
            record = matches[0]
        else:
            record = self.records[record_id]
            
        self._mark_accessed(record)
        
        trend = "stable"
        if len(record.revision_history) > 0:
            last_rev = record.revision_history[-1]
            if last_rev["new_confidence"] > last_rev["old_confidence"]:
                trend = "increasing"
            elif last_rev["new_confidence"] < last_rev["old_confidence"]:
                trend = "decreasing"
                
        return {
            "fact": record.fact,
            "how_we_know": f"First recorded from {record.source_type} on {record.created_at}",
            "confidence": record.current_confidence,
            "confidence_trend": trend,
            "confirmations": record.confirmations,
            "contradictions": record.contradictions,
            "sources": [{"type": record.source_type, "id": record.source_id, "date": record.created_at}],
            "revision_history": record.revision_history,
            "status": record.status
        }

    def search_facts(self, query: str, min_confidence: float = 0.0) -> list[ProvenanceRecord]:
        q = query.lower()
        results = [
            r for r in self.records.values()
            if q in r.fact.lower() and r.current_confidence >= min_confidence
        ]
        return results

    def get_uncertain_facts(self) -> list[ProvenanceRecord]:
        return [r for r in self.records.values() if r.status == "uncertain"]

    def get_stats(self) -> dict:
        total = len(self.records)
        active = sum(1 for r in self.records.values() if r.status == "active")
        superseded = sum(1 for r in self.records.values() if r.status == "superseded")
        retracted = sum(1 for r in self.records.values() if r.status == "retracted")
        uncertain = sum(1 for r in self.records.values() if r.status == "uncertain")
        
        total_conf = sum(r.current_confidence for r in self.records.values())
        avg_conf = total_conf / total if total > 0 else 0.0
        
        total_revisions = sum(len(r.revision_history) for r in self.records.values())
        
        return {
            "total_facts": total,
            "active": active,
            "superseded": superseded,
            "retracted": retracted,
            "uncertain": uncertain,
            "avg_confidence": avg_conf,
            "total_revisions": total_revisions
        }

    def decay_confidence(self, decay_rate: float = 0.001):
        now = datetime.now(UTC)
        for r in self.records.values():
            if r.status != "active":
                continue
            last_acc = datetime.fromisoformat(r.last_accessed)
            days = (now - last_acc).days
            if days > 0:
                decay = decay_rate * days
                new_conf = max(0.1, r.current_confidence - decay)
                if new_conf != r.current_confidence:
                    r.current_confidence = new_conf
                    r.last_accessed = now.isoformat()
        self._save()

provenance_tracker = ProvenanceTracker()
