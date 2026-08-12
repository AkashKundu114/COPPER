from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.ai.memory.vector_store import VectorStore
from app.core.constants import CHROMA_COLLECTION_CHAT, MEMORY_SEARCH_LIMIT
from app.core.logger import logger
from app.database.models.memory_v2 import UserMemoryV2, MemoryType, MemoryStatus, MEMORY_PRIORITY

chat_store = VectorStore(CHROMA_COLLECTION_CHAT)
doc_store = VectorStore("copper_documents")


class MemoryManager:
    def __init__(self):
        self.chat_store = chat_store
        self.doc_store = doc_store

    # ── Existing vector-store interaction log (unchanged) ──────────────────
    async def save_interaction(
        self,
        session_id: str,
        user_message: str,
        assistant_response: str,
        agent_type: str = "chat",
    ) -> None:
        combined = f"User: {user_message}\nAssistant: {assistant_response}"
        await self.chat_store.add(
            text=combined,
            metadata={
                "session_id": session_id,
                "agent_type": agent_type,
                "type": "interaction",
            },
        )

    async def search_relevant_context(
        self,
        query: str,
        session_id: Optional[str] = None,
        limit: int = MEMORY_SEARCH_LIMIT,
    ) -> str:
        where = {"session_id": session_id} if session_id else None
        results = await self.chat_store.search(query, n_results=limit, where=where)
        if not results:
            return ""
        context_parts = [r["document"] for r in results if r["distance"] < 1.2]
        return "\n\n".join(context_parts[:3])

    async def save_document(
        self,
        content: str,
        source: str,
        metadata: dict = None,
    ) -> str:
        meta = {"source": source, "type": "document"}
        if metadata:
            meta.update(metadata)
        return await self.doc_store.add(text=content, metadata=meta)

    async def search_documents(self, query: str, limit: int = 5) -> list[dict]:
        return await self.doc_store.search(query, n_results=limit)

    async def get_memory_stats(self) -> dict:
        return {
            "chat_memories": await self.chat_store.count(),
            "documents": await self.doc_store.count(),
        }

    # ── New: structured Fact/Observation/Hypothesis memory (Postgres) ─────
    # Master System Prompt §7-8, §29 (conflict resolution priority).

    def save_structured_memory(
        self,
        db: Session,
        content: str,
        memory_type: MemoryType,
        category: Optional[str] = None,
        source: str = "chat",
        confidence: float = 0.5,
        user_id: Optional[int] = None,
    ) -> UserMemoryV2:
        """
        Writes a new memory. Does NOT auto-supersede conflicting rows — that
        requires an explicit conflict-resolution pass (see resolve_conflicts
        below), since silently overwriting violates §8 ("do not blindly
        overwrite").
        """
        mem = UserMemoryV2(
            user_id=user_id,
            content=content,
            type=memory_type,
            category=category,
            source=source,
            confidence=confidence,
            evidence_count=1,
        )
        db.add(mem)
        db.commit()
        db.refresh(mem)
        logger.info(f"Saved {memory_type.value} memory: {content[:80]}")
        return mem

    def reinforce_memory(self, db: Session, memory_id: int, confidence_delta: float = 0.05) -> Optional[UserMemoryV2]:
        """Bumps evidence_count/confidence when a pattern repeats, and marks last_confirmed_at."""
        from datetime import datetime, timezone
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return None
        mem.evidence_count += 1
        mem.confidence = min(1.0, mem.confidence + confidence_delta)
        mem.last_confirmed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(mem)
        return mem

    def reject_memory(self, db: Session, memory_id: int) -> bool:
        """User marked a memory incorrect / asked to forget it."""
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return False
        mem.status = MemoryStatus.REJECTED
        db.commit()
        return True

    def get_relevant_structured_memories(
        self,
        db: Session,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> list[UserMemoryV2]:
        q = db.query(UserMemoryV2).filter(UserMemoryV2.status == MemoryStatus.ACTIVE)
        if category:
            q = q.filter(UserMemoryV2.category == category)
        return q.order_by(desc(UserMemoryV2.updated_at)).limit(limit).all()

    def resolve_conflicts(self, db: Session, category: str) -> Optional[UserMemoryV2]:
        """
        Given all active memories in a category, returns the one that wins
        per §29 priority: recent FACT > older FACT > repeated OBSERVATION >
        single OBSERVATION > HYPOTHESIS. Marks the losers SUPERSEDED.
        Caller decides whether to surface a "these conflict, which is right?"
        prompt to the user for genuinely ambiguous cases.
        """
        candidates = (
            db.query(UserMemoryV2)
            .filter(UserMemoryV2.category == category, UserMemoryV2.status == MemoryStatus.ACTIVE)
            .all()
        )
        if len(candidates) <= 1:
            return candidates[0] if candidates else None

        def sort_key(m: UserMemoryV2):
            return (MEMORY_PRIORITY[m.type], m.evidence_count, m.updated_at or m.created_at)

        winner = max(candidates, key=sort_key)
        for m in candidates:
            if m.id != winner.id:
                m.status = MemoryStatus.SUPERSEDED
                m.supersedes_id = winner.id
        db.commit()
        return winner


memory_manager = MemoryManager()
