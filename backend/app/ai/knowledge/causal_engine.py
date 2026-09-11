import json
import os
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
import uuid

from app.core.logger import logger
from app.ai.llm.ollama_client import ollama_client


@dataclass
class CausalEvent:
    event_id: str
    description: str
    timestamp: datetime
    category: str
    source: str
    entities: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["timestamp"] = self.timestamp.isoformat()
        return d

    @classmethod
    def from_dict(cls, data):
        data = data.copy()
        if "timestamp" in data and isinstance(data["timestamp"], str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class CausalLink:
    cause_id: str
    effect_id: str
    relationship: str
    confidence: float
    evidence: str = ""

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


@dataclass
class CausalChain:
    query: str
    chain: list[CausalEvent]
    links: list[CausalLink]
    explanation: str
    confidence: float


class CausalEngine:
    def __init__(self):
        self.events: dict[str, CausalEvent] = {}
        self.links: list[CausalLink] = []
        self.data_dir = "data"
        self.events_file = os.path.join(self.data_dir, "causal_events.json")
        self.links_file = os.path.join(self.data_dir, "causal_links.json")
        self._load()

    def _ensure_dir(self):
        os.makedirs(self.data_dir, exist_ok=True)

    def _save(self):
        self._ensure_dir()
        try:
            with open(self.events_file, "w") as f:
                json.dump({k: v.to_dict() for k, v in self.events.items()}, f, indent=2)
            with open(self.links_file, "w") as f:
                json.dump([l.to_dict() for l in self.links], f, indent=2)
        except Exception as e:
            logger.error(f"[CausalEngine] Error saving data: {e}")

    def _load(self):
        try:
            if os.path.exists(self.events_file):
                with open(self.events_file, "r") as f:
                    data = json.load(f)
                    self.events = {k: CausalEvent.from_dict(v) for k, v in data.items()}
            if os.path.exists(self.links_file):
                with open(self.links_file, "r") as f:
                    data = json.load(f)
                    self.links = [CausalLink.from_dict(v) for v in data]
        except Exception as e:
            logger.error(f"[CausalEngine] Error loading data: {e}")
            self.events = {}
            self.links = []

    def record_event(
        self,
        description: str,
        category: str,
        source: str,
        entities: list[str] | None = None,
        metadata: dict | None = None,
    ) -> CausalEvent:
        event = CausalEvent(
            event_id=str(uuid.uuid4()),
            description=description,
            timestamp=datetime.now(),
            category=category,
            source=source,
            entities=entities or [],
            metadata=metadata or {},
        )
        self.events[event.event_id] = event
        self._save()
        return event

    def add_causal_link(
        self, cause_id: str, effect_id: str, relationship: str, confidence: float, evidence: str = ""
    ) -> CausalLink:
        link = CausalLink(
            cause_id=cause_id,
            effect_id=effect_id,
            relationship=relationship,
            confidence=confidence,
            evidence=evidence,
        )
        self.links.append(link)
        self._save()
        return link

    def infer_links(self, window_hours: int = 24) -> list[CausalLink]:
        cutoff_time = datetime.now() - timedelta(hours=window_hours)
        recent_events = [e for e in self.events.values() if e.timestamp >= cutoff_time]
        recent_events.sort(key=lambda x: x.timestamp)
        new_links = []

        plausible_causes = {
            "action": ["outcome", "action"],
            "decision": ["action", "outcome"],
            "error": ["action"],
            "context_change": ["action", "decision"],
        }

        for i, earlier_event in enumerate(recent_events):
            for later_event in recent_events[i + 1:]:
                time_diff = later_event.timestamp - earlier_event.timestamp
                if time_diff > timedelta(minutes=30):
                    continue

                shared_entities = set(earlier_event.entities).intersection(set(later_event.entities))
                if not shared_entities:
                    continue

                if later_event.category not in plausible_causes.get(earlier_event.category, []):
                    continue

                entity_overlap_pct = len(shared_entities) / max(
                    len(set(earlier_event.entities).union(set(later_event.entities))), 1
                )
                
                # temporal proximity score: 1.0 at 0 minutes, 0.0 at 30 minutes
                temporal_proximity_score = max(0, 1.0 - (time_diff.total_seconds() / 1800.0))
                category_compatibility = 1.0

                confidence = (entity_overlap_pct * 0.5) + (temporal_proximity_score * 0.3) + (category_compatibility * 0.2)

                if confidence > 0.4:
                    link = CausalLink(
                        cause_id=earlier_event.event_id,
                        effect_id=later_event.event_id,
                        relationship="contributed_to",
                        confidence=confidence,
                        evidence=f"Inferred: shared entities {list(shared_entities)} within {int(time_diff.total_seconds() / 60)} mins.",
                    )
                    
                    # Avoid duplicates
                    if not any(
                        l.cause_id == link.cause_id and l.effect_id == link.effect_id for l in self.links
                    ):
                        self.links.append(link)
                        new_links.append(link)

        if new_links:
            self._save()
            logger.info(f"[CausalEngine] Inferred {len(new_links)} new causal links.")

        return new_links

    async def query_why(self, question: str) -> CausalChain:
        keywords = set(word.lower() for word in question.split() if len(word) > 3)
        
        matches = []
        for e in self.events.values():
            text_to_search = (e.description + " " + " ".join(e.entities)).lower()
            if any(k in text_to_search for k in keywords):
                matches.append(e)
                
        matches.sort(key=lambda x: x.timestamp, reverse=True)
        
        if not matches:
            return CausalChain(
                query=question,
                chain=[],
                links=[],
                explanation="Could not find relevant events for this query.",
                confidence=0.0
            )

        target_event = matches[0]
        chain_events = self.get_event_causes(target_event.event_id, depth=3)
        chain_events.insert(0, target_event)  # Prepend the target event
        chain_events.sort(key=lambda x: x.timestamp)
        
        event_ids = {e.event_id for e in chain_events}
        chain_links = [l for l in self.links if l.cause_id in event_ids and l.effect_id in event_ids]
        
        overall_confidence = sum(l.confidence for l in chain_links) / max(len(chain_links), 1) if chain_links else 0.5
        
        timeline_strs = [f"{e.timestamp.strftime('%H:%M:%S')}: {e.description}" for e in chain_events]
        basic_expl = "Timeline:\n" + "\n".join(timeline_strs)
        
        explanation = basic_expl
        if await ollama_client.is_available():
            prompt = f"Explain the causal chain for the question '{question}' based on these events:\n{basic_expl}\nKeep it brief and clear."
            try:
                explanation = await ollama_client.generate(prompt)
            except Exception as e:
                logger.warning(f"[CausalEngine] LLM generation failed for causal explanation: {e}")

        return CausalChain(
            query=question,
            chain=chain_events,
            links=chain_links,
            explanation=explanation,
            confidence=overall_confidence
        )

    def get_event_causes(self, event_id: str, depth: int = 5) -> list[CausalEvent]:
        causes = set()
        current_layer = {event_id}
        
        for _ in range(depth):
            next_layer = set()
            for eid in current_layer:
                for link in self.links:
                    if link.effect_id == eid and link.cause_id in self.events:
                        next_layer.add(link.cause_id)
                        causes.add(link.cause_id)
            current_layer = next_layer
            if not current_layer:
                break
                
        return [self.events[eid] for eid in causes]

    def get_event_effects(self, event_id: str, depth: int = 5) -> list[CausalEvent]:
        effects = set()
        current_layer = {event_id}
        
        for _ in range(depth):
            next_layer = set()
            for eid in current_layer:
                for link in self.links:
                    if link.cause_id == eid and link.effect_id in self.events:
                        next_layer.add(link.effect_id)
                        effects.add(link.effect_id)
            current_layer = next_layer
            if not current_layer:
                break
                
        return [self.events[eid] for eid in effects]

    def get_timeline(self, hours: int = 24, category: str | None = None) -> list[CausalEvent]:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        events = [e for e in self.events.values() if e.timestamp >= cutoff_time]
        if category:
            events = [e for e in events if e.category == category]
        events.sort(key=lambda x: x.timestamp)
        return events

    def get_stats(self) -> dict:
        categories = {}
        for e in self.events.values():
            categories[e.category] = categories.get(e.category, 0) + 1
            
        return {
            "total_events": len(self.events),
            "total_links": len(self.links),
            "avg_chain_length": 0, # Placeholder
            "categories_breakdown": categories
        }


causal_engine = CausalEngine()
