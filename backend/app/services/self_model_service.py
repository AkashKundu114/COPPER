import math
import re
import uuid
from datetime import UTC, datetime

from sqlalchemy import desc

from app.ai.memory.vector_store import VectorStore
from app.core.logger import logger
from app.database.models.self_memory import SelfMemory, SelfMemoryCategory, SelfMemoryOutcome
from app.database.postgres import SessionLocal

_self_memory_store = VectorStore("copper_self_memory")


class SelfModelService:
    LEARNING_RATE = 0.15
    DECAY_RATES = {
        SelfMemoryCategory.DECISION: 0.005,
        SelfMemoryCategory.CORRECTION: 0.03,
        SelfMemoryCategory.POSITION: 0.005,
        SelfMemoryCategory.TRACK_RECORD: 0.005,
        SelfMemoryCategory.OPEN_QUESTION: 0.10,
    }
    CORRECTION_PATTERNS = [
        r"\bno[,.]?\s+(?:that'?s?\s+)?(?:wrong|incorrect|not right)",
        r"\bactually[,.]?\s+(?:I|i)\s+(?:prefer|want|need|meant)",
        r"\bthat'?s?\s+not\s+(?:what|how|right)",
        r"\bdon'?t\s+do\s+(?:that|it)\s+(?:that|this)\s+way",
        r"\bstop\s+(?:doing|suggesting)\b",
        r"\bi\s+(?:already|never)\s+(?:told|said|mentioned)",
        r"\bcorrection:\s",
    ]

    async def build_self_context(self, message: str) -> str:
        """Build the self_context_snippet for the system prompt."""
        db = SessionLocal()
        try:
            open_qs = (
                db.query(SelfMemory)
                .filter(
                    SelfMemory.category == SelfMemoryCategory.OPEN_QUESTION,
                    SelfMemory.outcome.is_(None),
                )
                .order_by(desc(SelfMemory.created_at))
                .limit(2)
                .all()
            )

            relevant = []
            try:
                results = await _self_memory_store.search(message, n_results=5)
                if results:
                    for r in results:
                        mem_id = r.get("metadata", {}).get("self_memory_id")
                        if mem_id:
                            mem = db.query(SelfMemory).filter(SelfMemory.id == mem_id).first()
                            if mem:
                                cosine_sim = max(0, 1 - r.get("distance", 1))
                                score = 0.6 * cosine_sim + 0.4 * mem.confidence
                                relevant.append((mem, score))
            except Exception as e:
                logger.warning(f"Self-memory vector search fallback: {e}")

            relevant.sort(key=lambda x: x[1], reverse=True)
            top_memories = [m for m, _ in relevant[:3]]

            seen_ids = {m.id for m in top_memories}
            for oq in open_qs:
                if oq.id not in seen_ids:
                    top_memories.append(oq)

            if not top_memories:
                return ""

            lines = []
            for mem in top_memories:
                cat = mem.category.value.upper().replace("_", " ")
                outcome_tag = f" [{mem.outcome.value}]" if mem.outcome else ""
                lines.append(
                    f"- [{cat}]{outcome_tag} {mem.content} (confidence: {mem.confidence:.0%}, evidence: {mem.evidence_count}x)"
                )

            return "\n".join(lines)
        finally:
            db.close()

    def detect_correction(self, user_message: str) -> bool:
        """Check if a user message contains a correction."""
        lower = user_message.lower().strip()
        for pattern in self.CORRECTION_PATTERNS:
            if re.search(pattern, lower):
                return True
        return False

    async def record_correction(self, user_message: str, copper_response: str, session_id: str) -> SelfMemory | None:
        """Detect and record user corrections."""
        if not self.detect_correction(user_message):
            return None

        content = (
            f"User corrected COPPER: '{user_message[:200]}'. Previous response was about: '{copper_response[:150]}'"
        )
        return await self._create_entry(
            category=SelfMemoryCategory.CORRECTION,
            content=content,
            confidence=0.8,
        )

    async def record_decision(
        self, agent_type: str, decision: str, context: str, episode_id: int | None = None
    ) -> SelfMemory | None:
        """Record a significant decision COPPER made."""
        if len(decision) < 20:
            return None
        content = f"Decided via {agent_type}: {decision[:300]}"
        return await self._create_entry(
            category=SelfMemoryCategory.DECISION,
            content=content,
            confidence=0.5,
            related_episode_id=episode_id,
        )

    async def record_guardian_outcome(self, verdict_level: str, reasoning: str, user_action: str) -> SelfMemory | None:
        """Record the outcome of a Guardian challenge."""
        content = f"Guardian {verdict_level}: {reasoning[:200]}. User chose: {user_action}"
        outcome = (
            SelfMemoryOutcome.CONFIRMED_HELPFUL
            if user_action in ("follow_rec", "Follow Rec")
            else SelfMemoryOutcome.UNKNOWN
        )
        return await self._create_entry(
            category=SelfMemoryCategory.TRACK_RECORD,
            content=content,
            confidence=0.7,
            outcome=outcome,
        )

    async def record_reflection(
        self, content: str, category: SelfMemoryCategory = SelfMemoryCategory.POSITION, confidence: float = 0.5
    ) -> SelfMemory | None:
        """Record a reflection from the background reflection cycle."""
        return await self._create_entry(
            category=category,
            content=content,
            confidence=confidence,
        )

    async def _create_entry(
        self,
        category: SelfMemoryCategory,
        content: str,
        confidence: float = 0.5,
        outcome: SelfMemoryOutcome | None = None,
        related_episode_id: int | None = None,
    ) -> SelfMemory | None:
        """Create a self_memory row and index in vector store."""
        db = SessionLocal()
        try:
            entry = SelfMemory(
                id=str(uuid.uuid4()),
                category=category,
                content=content,
                outcome=outcome,
                confidence=confidence,
                related_episode_id=related_episode_id,
            )
            db.add(entry)
            db.commit()
            db.refresh(entry)

            try:
                await _self_memory_store.add(
                    text=content,
                    metadata={"self_memory_id": entry.id, "category": category.value},
                )
            except Exception as e:
                logger.warning(f"Failed to index self-memory in vector store: {e}")

            logger.info(f"Self-memory recorded: [{category.value}] {content[:80]}")
            return entry
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to record self-memory: {e}")
            return None
        finally:
            db.close()

    def apply_bayesian_update(self, memory_id: str) -> bool:
        """Reinforce a self-memory entry using the Bayesian formula:"""
        db = SessionLocal()
        try:
            mem = db.query(SelfMemory).filter(SelfMemory.id == memory_id).first()
            if not mem:
                return False
            mem.evidence_count += 1
            c_old = mem.confidence
            c_new = c_old + (1 - c_old) * self.LEARNING_RATE * math.log2(1 + mem.evidence_count)
            mem.confidence = min(c_new, 0.99)
            mem.last_reinforced_at = datetime.now(UTC)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Bayesian update failed for {memory_id}: {e}")
            return False
        finally:
            db.close()

    def apply_decay(self) -> int:
        """Apply temporal decay to all self-memory entries."""
        db = SessionLocal()
        try:
            entries = db.query(SelfMemory).filter(SelfMemory.superseded_by.is_(None)).all()
            updated = 0
            now = datetime.now(UTC)
            for entry in entries:
                ref_time = entry.last_reinforced_at or entry.created_at
                if ref_time is None:
                    continue
                if ref_time.tzinfo is None:
                    ref_time = ref_time.replace(tzinfo=UTC)
                delta_days = (now - ref_time).total_seconds() / 86400
                if delta_days < 0.1:
                    continue
                decay_rate = self.DECAY_RATES.get(entry.category, 0.03)
                new_conf = entry.confidence * math.exp(-decay_rate * delta_days)
                if abs(new_conf - entry.confidence) > 0.001:
                    entry.confidence = max(new_conf, 0.01)
                    updated += 1
            db.commit()
            if updated:
                logger.info(f"Self-memory decay applied to {updated} entries")
            return updated
        except Exception as e:
            db.rollback()
            logger.error(f"Self-memory decay failed: {e}")
            return 0
        finally:
            db.close()

    def resolve(self, memory_id: str) -> bool:
        """Mark an open_question or correction as integrated."""
        db = SessionLocal()
        try:
            mem = db.query(SelfMemory).filter(SelfMemory.id == memory_id).first()
            if not mem:
                return False
            mem.outcome = SelfMemoryOutcome.CONFIRMED_HELPFUL
            mem.last_reinforced_at = datetime.now(UTC)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to resolve self-memory {memory_id}: {e}")
            return False
        finally:
            db.close()

    def get_all(self, category: str | None = None, limit: int = 50) -> list[dict]:
        """Get all self-memory entries, optionally filtered by category."""
        db = SessionLocal()
        try:
            q = db.query(SelfMemory).order_by(desc(SelfMemory.created_at))
            if category:
                try:
                    cat_enum = SelfMemoryCategory(category)
                    q = q.filter(SelfMemory.category == cat_enum)
                except ValueError:
                    pass
            entries = q.limit(limit).all()
            return [e.to_dict() for e in entries]
        finally:
            db.close()


self_model_service = SelfModelService()
