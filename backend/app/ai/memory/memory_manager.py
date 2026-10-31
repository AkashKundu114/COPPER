import math
from datetime import UTC, datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai.memory.vector_store import VectorStore
from app.core.constants import CHROMA_COLLECTION_CHAT, MEMORY_SEARCH_LIMIT
from app.core.logger import logger
from app.database.models.memory_v2 import MEMORY_PRIORITY, MemoryStatus, MemoryType, UserMemoryV2

PROVENANCE_WEIGHTS: dict[str, float] = {
    "explicit_user": 1.00,
    "user_explicit": 1.00,
    "user_directive": 1.00,
    "user_verified": 1.00,
    "system_verified": 0.95,
    "local_file": 0.85,
    "file_system": 0.85,
    "tool_success": 0.85,
    "observation": 0.75,
    "chat": 0.50,
    "web_search": 0.35,
    "ambient_inferred": 0.25,
    "external_untrusted": 0.15,
    "ext_untrusted": 0.15,
    "speculative": 0.15,
    "injected": 0.10,
}

DECAY_CONSTANTS: dict[MemoryType, float] = {
    MemoryType.FACT: 0.005,
    MemoryType.OBSERVATION: 0.030,
    MemoryType.HYPOTHESIS: 0.100,
}


def compute_unified_epistemic_decay(
    confidence: float,
    mem_type: MemoryType,
    elapsed_days: float,
    importance: float = 0.50,
    retrieval_count: int = 0,
) -> float:
    """UMF-EDR (Unified Multi-Factor Epistemic Decay and Reinforcement):"""
    lam_base = DECAY_CONSTANTS.get(mem_type, 0.030)
    beta_plasticity = 0.40
    lam_eff = lam_base / (1.0 + beta_plasticity * math.log(1.0 + max(0, retrieval_count)))

    c_floor = min(confidence, 0.05 + (0.50 * max(0.0, min(1.0, importance))))
    decayed = confidence * math.exp(-lam_eff * max(0.0, elapsed_days))
    return max(c_floor, min(0.99, decayed))


compute_temporal_decay = compute_unified_epistemic_decay


def compute_unified_retrieval_score(
    semantic_distance: float,
    confidence: float,
    importance: float = 0.50,
    alpha_rel: float = 0.50,
    alpha_conf: float = 0.35,
    alpha_imp: float = 0.15,
) -> float:
    """UMF-EDR Unified Context Scoring Function:"""
    relevance = max(0.0, min(1.0, 1.0 - (semantic_distance / 2.0)))
    score = (alpha_rel * relevance) + (alpha_conf * confidence) + (alpha_imp * importance)
    return round(score, 4)


def compute_surprise_gated_log_odds(
    current_confidence: float,
    mem_type: MemoryType,
    elapsed_days: float,
    provenance_source: str = "chat",
    polarity: int = 1,
    importance: float = 0.50,
    retrieval_count: int = 0,
) -> float:
    """PW-EBR Algorithm with UMF-EDR integration:
    Calculates surprise-gated log-odds updates using natural units (nats)
    matching the natural log-odds belief metric space.
    """
    c_prior = compute_unified_epistemic_decay(current_confidence, mem_type, elapsed_days, importance, retrieval_count)
    c_prior = max(0.01, min(0.99, c_prior))

    l_prior = math.log(c_prior / (1.0 - c_prior))

    target_y = 1.0 if polarity > 0 else 0.0
    # Natural information unit (nats) surprise: -ln(P(outcome))
    surprise = -math.log(max(1e-4, 1.0 - abs(c_prior - target_y) + 1e-4))

    gamma_s = PROVENANCE_WEIGHTS.get(provenance_source.lower(), 0.50)

    scale = 2.5 if gamma_s >= 0.90 else (1.8 if gamma_s >= 0.70 else 1.0)
    delta_l = polarity * gamma_s * min(3.5, surprise * scale)
    l_new = l_prior + delta_l

    c_new = 1.0 / (1.0 + math.exp(-l_new))
    c_floor = 0.05 if polarity < 0 else min(current_confidence, 0.05 + (0.50 * max(0.0, min(1.0, importance))))
    return round(max(c_floor, min(0.99, c_new)), 3)


def update_epistemic_tier(mem: UserMemoryV2) -> None:
    """Symmetric epistemic status transitions based on calibrated confidence thresholds.
    Enforces bidirectional promotion and demotion:
      - >= 0.85: FACT
      - 0.50 <= C < 0.85: OBSERVATION
      - < 0.50: HYPOTHESIS
    """
    if mem.confidence >= 0.85:
        if mem.type != MemoryType.FACT:
            logger.info(f"[PW-EBR/UMF-EDR] Memory promoted to FACT: ID {mem.id} (Confidence: {mem.confidence})")
            mem.type = MemoryType.FACT
    elif mem.confidence >= 0.50:
        if mem.type != MemoryType.OBSERVATION:
            logger.info(f"[PW-EBR/UMF-EDR] Memory transitioned to OBSERVATION: ID {mem.id} (Confidence: {mem.confidence})")
            mem.type = MemoryType.OBSERVATION
    else:
        if mem.type != MemoryType.HYPOTHESIS:
            logger.info(f"[PW-EBR/UMF-EDR] Memory demoted to HYPOTHESIS: ID {mem.id} (Confidence: {mem.confidence})")
            mem.type = MemoryType.HYPOTHESIS


chat_store = VectorStore(CHROMA_COLLECTION_CHAT)
doc_store = VectorStore("copper_documents")


class MemoryManager:
    def __init__(self):
        self.chat_store = chat_store
        self.doc_store = doc_store

    async def save_interaction(
        self, session_id: str, user_message: str, assistant_response: str, agent_type: str = "chat"
    ) -> None:
        from app.ai.llm.prompt_manager import is_corrupted_content

        if not assistant_response or len(assistant_response.strip()) < 3:
            return
        if is_corrupted_content(assistant_response):
            return
        if any(
            err in assistant_response
            for err in [
                "Cannot reach local Ollama",
                "Cannot reach the local Ollama",
                "No models currently found",
                "No models are currently downloaded",
                "Ollama model '",
                "Ollama returned status",
                "pre-stored version based on my last update",
            ]
        ):
            return

        combined = f"User: {user_message}\nAssistant: {assistant_response}"
        doc_id = await self.chat_store.add(
            text=combined,
            metadata={
                "session_id": session_id,
                "agent_type": agent_type,
                "type": "interaction",
                "timestamp": datetime.now(UTC).isoformat(),
            },
        )
        from app.ai.memory.bm25_index import bm25_index

        bm25_index.add_document(
            doc_id=doc_id, text=combined, metadata={"session_id": session_id, "agent_type": agent_type}
        )

    async def get_recent_context(self, session_id: str, limit: int = 5) -> str:
        from app.ai.llm.prompt_manager import is_corrupted_content

        results = await self.chat_store.search(session_id, n_results=limit)
        context_parts = [
            r["document"] for r in results if r["distance"] < 1.2 and not is_corrupted_content(r["document"])
        ]
        return "\n\n".join(context_parts[:3])

    async def get_relevant_memories(self, query: str, limit: int = MEMORY_SEARCH_LIMIT) -> list[dict]:
        from app.ai.llm.prompt_manager import is_corrupted_content

        results = await self.chat_store.search(query, n_results=limit)
        memories = []
        now = datetime.now(UTC)
        for r in results:
            dist = r.get("distance", 99.0)
            if dist < 1.5:
                doc = r.get("document", "")
                if is_corrupted_content(doc):
                    continue
                if any(
                    err in doc
                    for err in [
                        "Cannot reach local Ollama",
                        "Cannot reach the local Ollama",
                        "No models currently found",
                        "No models are currently downloaded",
                        "Ollama model '",
                        "Ollama returned status",
                        "pre-stored version based on my last update",
                    ]
                ):
                    continue
                meta = r.get("metadata", {})
                mem_type_str = meta.get("type", "observation")
                mem_type = (
                    MemoryType.FACT
                    if mem_type_str == "fact"
                    else (MemoryType.HYPOTHESIS if mem_type_str == "hypothesis" else MemoryType.OBSERVATION)
                )
                confidence = float(meta.get("confidence", 0.85 if mem_type == MemoryType.FACT else 0.50))
                importance = float(meta.get("importance", 0.90 if mem_type == MemoryType.FACT else 0.50))
                retrieval_count = int(meta.get("retrieval_count", 0))

                # Dynamic retrieval-time decay computation if timestamp is present
                ts_str = meta.get("timestamp")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str)
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=UTC)
                        elapsed_days = max(0.0, (now - ts).total_seconds() / 86400.0)
                        confidence = compute_unified_epistemic_decay(
                            confidence, mem_type, elapsed_days, importance, retrieval_count
                        )
                    except Exception:
                        pass

                unified_score = compute_unified_retrieval_score(dist, confidence, importance)

                mem_id = meta.get("id", str(r.get("id", f"mem_{len(memories)}")))
                prov = meta.get("provenance", meta.get("source", "chat"))
                memories.append(
                    {
                        "id": mem_id,
                        "provenance": prov,
                        "content": doc,
                        "memory_type": mem_type.value,
                        "distance": dist,
                        "confidence": confidence,
                        "importance": importance,
                        "unified_score": unified_score,
                    }
                )
        memories.sort(key=lambda m: m.get("unified_score", 0.0), reverse=True)
        return memories

    async def save_document(self, content: str, source: str, metadata: dict = None) -> str:
        meta = {"source": source, "type": "document", "timestamp": datetime.now(UTC).isoformat()}
        if metadata:
            meta.update(metadata)
        doc_id = await self.doc_store.add(text=content, metadata=meta)
        try:
            from app.ai.memory.hybrid_retriever import hybrid_retriever

            await hybrid_retriever.index_document(doc_id=doc_id, content=content, metadata=meta)
        except Exception as e:
            logger.debug(f"Hybrid indexing skipped/fallback: {e}")
        return doc_id

    async def search_documents(self, query: str, limit: int = 5) -> list[dict]:
        try:
            from app.ai.memory.hybrid_retriever import hybrid_retriever

            if hybrid_retriever._initialized:
                return await hybrid_retriever.retrieve(query, top_k=limit)
        except Exception as e:
            logger.warning(f"Hybrid search fallback to vector store: {e}")
        return await self.doc_store.search(query, n_results=limit)

    async def get_memory_stats(self) -> dict:
        return {"chat_memories": await self.chat_store.count(), "documents": await self.doc_store.count()}

    def save_structured_memory(
        self,
        db: Session,
        content: str,
        memory_type: MemoryType,
        category: str | None = None,
        source: str = "chat",
        confidence: float = 0.5,
        importance: float | None = None,
        user_id: int | None = None,
    ) -> UserMemoryV2:
        if importance is None:
            importance = (
                0.90 if memory_type == MemoryType.FACT else (0.50 if memory_type == MemoryType.OBSERVATION else 0.25)
            )
        mem = UserMemoryV2(
            user_id=user_id,
            content=content,
            type=memory_type,
            category=category,
            source=source,
            confidence=confidence,
            evidence_count=1,
            extra_metadata={"importance": importance, "retrieval_count": 0},
        )
        update_epistemic_tier(mem)
        db.add(mem)
        db.commit()
        db.refresh(mem)
        logger.info(f"Saved {mem.type.value} memory (Importance: {importance:.2f}): {content[:80]}")
        return mem

    def reinforce_memory(
        self,
        db: Session,
        memory_id: int,
        confidence_delta: float | None = None,
        provenance: str = "chat",
        polarity: int = 1,
    ) -> UserMemoryV2 | None:
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return None

        now = datetime.now(UTC)
        last_time = mem.last_confirmed_at or mem.updated_at or mem.created_at
        if last_time:
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=UTC)
            elapsed_days = max(0.0, (now - last_time).total_seconds() / 86400.0)
        else:
            elapsed_days = 0.0

        mem.evidence_count += 1

        if confidence_delta is not None and confidence_delta != 0.05:
            if polarity < 0:
                mem.confidence = max(0.05, mem.confidence - abs(confidence_delta))
            else:
                mem.confidence = min(0.99, mem.confidence + abs(confidence_delta))
        else:
            mem.confidence = compute_surprise_gated_log_odds(
                current_confidence=mem.confidence,
                mem_type=mem.type,
                elapsed_days=elapsed_days,
                provenance_source=provenance,
                polarity=polarity,
                importance=mem.importance,
                retrieval_count=mem.retrieval_count,
            )

        update_epistemic_tier(mem)

        mem.last_confirmed_at = now
        db.commit()
        db.refresh(mem)
        return mem

    def contradict_memory(
        self,
        db: Session,
        memory_id: int,
        provenance: str = "chat",
        confidence_delta: float | None = None,
    ) -> UserMemoryV2 | None:
        """Apply negative epistemic belief update (contradiction) to memory."""
        return self.reinforce_memory(
            db=db,
            memory_id=memory_id,
            confidence_delta=confidence_delta,
            provenance=provenance,
            polarity=-1,
        )

    def record_retrieval(self, db: Session, memory_id: int) -> UserMemoryV2 | None:
        """UMF-EDR Closed-Loop Retrieval Plasticity (Testing / Spacing Effect):
        Increments retrieval count to retard future temporal decay without fabricating
        artificial confidence without evidence.
        """
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return None
        mem.retrieval_count += 1
        db.commit()
        db.refresh(mem)
        return mem

    def reject_memory(self, db: Session, memory_id: int) -> bool:
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return False
        mem.status = MemoryStatus.REJECTED
        db.commit()
        return True

    def quarantine_memory(self, db: Session, memory_id: int) -> bool:
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return False
        mem.status = MemoryStatus.QUARANTINED
        db.commit()
        return True

    def archive_memory(self, db: Session, memory_id: int) -> bool:
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return False
        mem.status = MemoryStatus.ARCHIVED
        db.commit()
        return True

    def expire_memory(self, db: Session, memory_id: int) -> bool:
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return False
        mem.status = MemoryStatus.EXPIRED
        db.commit()
        return True

    def gc_expired_memories(self, db: Session, max_age_days: float = 180.0) -> int:
        """Deterministically expires or archives stale hypotheses below floor without deleting facts."""
        now = datetime.now(UTC)
        candidates = (
            db.query(UserMemoryV2)
            .filter(
                UserMemoryV2.status == MemoryStatus.ACTIVE,
                UserMemoryV2.type == MemoryType.HYPOTHESIS,
                UserMemoryV2.confidence < 0.20,
            )
            .all()
        )
        count = 0
        for m in candidates:
            last_t = m.last_confirmed_at or m.updated_at or m.created_at
            if last_t:
                if last_t.tzinfo is None:
                    last_t = last_t.replace(tzinfo=UTC)
                age = (now - last_t).total_seconds() / 86400.0
                if age > max_age_days:
                    m.status = MemoryStatus.EXPIRED
                    count += 1
        if count > 0:
            db.commit()
        return count

    def get_relevant_structured_memories(
        self, db: Session, category: str | None = None, limit: int = 20
    ) -> list[UserMemoryV2]:
        q = db.query(UserMemoryV2).filter(UserMemoryV2.status == MemoryStatus.ACTIVE)
        if category:
            q = q.filter(UserMemoryV2.category == category)
        return q.order_by(desc(UserMemoryV2.updated_at)).limit(limit).all()

    # Alias for ContextEngine compatibility
    get_active_memories = get_relevant_structured_memories

    def resolve_conflicts(
        self, db: Session, category: str, attribute: str | None = None
    ) -> UserMemoryV2 | None:
        q = db.query(UserMemoryV2).filter(
            UserMemoryV2.category == category, UserMemoryV2.status == MemoryStatus.ACTIVE
        )
        candidates = q.all()
        if attribute:
            candidates = [
                m for m in candidates if m.extra_metadata and m.extra_metadata.get("attribute") == attribute
            ]
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
