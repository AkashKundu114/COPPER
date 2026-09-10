import math
from datetime import UTC, datetime

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai.memory.vector_store import VectorStore
from app.core.constants import CHROMA_COLLECTION_CHAT, MEMORY_SEARCH_LIMIT
from app.core.logger import logger
from app.database.models.memory_v2 import MEMORY_PRIORITY, MemoryStatus, MemoryType, UserMemoryV2

# PW-EBR: Provenance-Weighted Epistemic Belief Revision Constants
PROVENANCE_WEIGHTS: dict[str, float] = {
    "explicit_user": 1.00,  # Direct explicit command or correction from user
    "user_directive": 1.00,
    "tool_success": 0.85,  # Verified sandbox execution or compiler pass
    "system_verified": 0.75,  # Confirmed system interaction
    "chat": 0.50,  # Standard multi-turn dialog observation
    "observation": 0.50,
    "ambient_inferred": 0.25,  # Inferred pattern or background hypothesis
    "speculative": 0.15,
}

DECAY_CONSTANTS: dict[MemoryType, float] = {
    MemoryType.FACT: 0.005,  # Half-life ~138 days
    MemoryType.OBSERVATION: 0.030,  # Half-life ~23 days
    MemoryType.HYPOTHESIS: 0.100,  # Half-life ~7 days
}


def compute_unified_epistemic_decay(
    confidence: float,
    mem_type: MemoryType,
    elapsed_days: float,
    importance: float = 0.50,
    retrieval_count: int = 0,
) -> float:
    """
    UMF-EDR (Unified Multi-Factor Epistemic Decay and Reinforcement):
    Integrates:
    1. Base tier decay constants (lambda_Fact=0.005, lambda_Obs=0.030, lambda_Hyp=0.100).
    2. Spacing / Testing Effect: Retrieval-Induced Plasticity:
       lambda_eff = lambda_T / (1.0 + beta * ln(1 + N_retrievals))
    3. Importance-Bounded Confidence Floor:
       C_floor = C_min + (C_base_floor - C_min) * Importance
    Formula:
       C(t) = max(C_floor, C_0 * exp(-lambda_eff * delta_t))
    """
    lam_base = DECAY_CONSTANTS.get(mem_type, 0.030)
    beta_plasticity = 0.40
    lam_eff = lam_base / (1.0 + beta_plasticity * math.log(1.0 + max(0, retrieval_count)))

    # Importance-bounded resistance floor (high-importance memories never decay below floor)
    c_floor = 0.05 + (0.50 * max(0.0, min(1.0, importance)))
    decayed = confidence * math.exp(-lam_eff * max(0.0, elapsed_days))
    return max(c_floor, min(0.99, decayed))


# Backward-compatible alias
compute_temporal_decay = compute_unified_epistemic_decay


def compute_unified_retrieval_score(
    semantic_distance: float,
    confidence: float,
    importance: float = 0.50,
    alpha_rel: float = 0.50,
    alpha_conf: float = 0.35,
    alpha_imp: float = 0.15,
) -> float:
    """
    UMF-EDR Unified Context Scoring Function:
    S_unified = alpha_rel * Relevance(v_q, v_m) + alpha_conf * Confidence(m) + alpha_imp * Importance(m)
    where Relevance = max(0.0, 1.0 - (distance / 2.0))
    """
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
    """
    PW-EBR Algorithm with UMF-EDR integration:
    L_{t+1} = L_prior * exp(-lambda_eff * delta_t) + gamma_s * Surprise * polarity
    where Surprise = -log2(1 - |C_prior - y| + 1e-4)
    and C_{new} = 1 / (1 + exp(-L_{t+1}))
    """
    # 1. Decay prior confidence over elapsed time using UMF-EDR multi-factor formulation
    c_prior = compute_unified_epistemic_decay(current_confidence, mem_type, elapsed_days, importance, retrieval_count)
    c_prior = max(0.01, min(0.99, c_prior))

    # 2. Prior log-odds
    l_prior = math.log(c_prior / (1.0 - c_prior))

    # 3. Information-theoretic surprise calculation
    target_y = 1.0 if polarity > 0 else 0.0
    surprise = -math.log2(max(1e-4, 1.0 - abs(c_prior - target_y) + 1e-4))

    # 4. Provenance weighting factor
    gamma_s = PROVENANCE_WEIGHTS.get(provenance_source.lower(), 0.50)

    # 5. Updated log-odds with provenance-scaled surprise step
    scale = 2.5 if gamma_s >= 0.90 else (1.8 if gamma_s >= 0.70 else 1.0)
    delta_l = polarity * gamma_s * min(3.5, surprise * scale)
    l_new = l_prior + delta_l

    # 6. Convert back to confidence probability
    c_new = 1.0 / (1.0 + math.exp(-l_new))
    return round(max(0.05, min(0.99, c_new)), 3)


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
            for err in ["Ollama returned status", "Cannot reach local Ollama", "Error connecting to Ollama"]
        ):
            return

        combined = f"User: {user_message}\nAssistant: {assistant_response}"
        doc_id = await self.chat_store.add(
            text=combined, metadata={"session_id": session_id, "agent_type": agent_type, "type": "interaction"}
        )
        try:
            from app.ai.memory.bm25_index import bm25_index

            bm25_index.add_document(
                doc_id=doc_id,
                content=combined,
                metadata={"session_id": session_id, "agent_type": agent_type, "type": "interaction"},
                source="chat",
            )
        except Exception as bm_err:
            logger.debug(f"BM25 chat indexing skipped: {bm_err}")

    async def search_relevant_context(
        self, query: str, session_id: str | None = None, limit: int = MEMORY_SEARCH_LIMIT
    ) -> str:
        from app.ai.llm.prompt_manager import is_corrupted_content

        where = {"session_id": session_id} if session_id else None
        results = await self.chat_store.search(query, n_results=limit, where=where)
        if not results:
            return ""
        context_parts = [
            r["document"] for r in results if r["distance"] < 1.2 and not is_corrupted_content(r["document"])
        ]
        return "\n\n".join(context_parts[:3])

    async def get_relevant_memories(self, query: str, limit: int = MEMORY_SEARCH_LIMIT) -> list[dict]:
        from app.ai.llm.prompt_manager import is_corrupted_content

        results = await self.chat_store.search(query, n_results=limit)
        memories = []
        for r in results:
            dist = r.get("distance", 99.0)
            if dist < 1.5:
                doc = r.get("document", "")
                if is_corrupted_content(doc):
                    continue
                meta = r.get("metadata", {})
                mem_type = meta.get("type", "observation")
                confidence = float(meta.get("confidence", 0.85 if mem_type == "fact" else 0.50))
                importance = float(meta.get("importance", 0.90 if mem_type == "fact" else 0.50))
                unified_score = compute_unified_retrieval_score(dist, confidence, importance)

                memories.append(
                    {
                        "content": doc,
                        "memory_type": mem_type,
                        "distance": dist,
                        "confidence": confidence,
                        "importance": importance,
                        "unified_score": unified_score,
                    }
                )
        # Sort by UMF-EDR unified ranking score descending
        memories.sort(key=lambda m: m.get("unified_score", 0.0), reverse=True)
        return memories

    async def save_document(self, content: str, source: str, metadata: dict = None) -> str:
        meta = {"source": source, "type": "document"}
        if metadata:
            meta.update(metadata)
        doc_id = await self.doc_store.add(text=content, metadata=meta)
        try:
            from app.ai.memory.bm25_index import bm25_index

            bm25_index.add_document(doc_id=doc_id, content=content, metadata=meta, source=source)
        except Exception as bm_err:
            logger.debug(f"BM25 document indexing skipped: {bm_err}")
        return doc_id

    async def search_documents(self, query: str, limit: int = 5, use_hybrid: bool = True) -> list[dict]:
        if use_hybrid:
            try:
                from app.ai.memory.hybrid_search import hybrid_search

                hybrid_results = await hybrid_search.search(query, limit=limit)
                docs = []
                for h in hybrid_results:
                    docs.append(
                        {
                            "document": h.get("content", ""),
                            "metadata": h.get("metadata", {}),
                            "distance": h.get("vector_distance", 1.0),
                            "rrf_score": h.get("rrf_score", 0.0),
                            "source": h.get("source", "document"),
                        }
                    )
                return docs
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
        db.add(mem)
        db.commit()
        db.refresh(mem)
        logger.info(f"Saved {memory_type.value} memory (Importance: {importance:.2f}): {content[:80]}")
        return mem

    def reinforce_memory(
        self,
        db: Session,
        memory_id: int,
        confidence_delta: float | None = None,
        provenance: str = "chat",
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
            mem.confidence = min(0.99, mem.confidence + confidence_delta)
        else:
            # Novelty 2: PW-EBR with UMF-EDR Multi-Factor Scaling
            mem.confidence = compute_surprise_gated_log_odds(
                current_confidence=mem.confidence,
                mem_type=mem.type,
                elapsed_days=elapsed_days,
                provenance_source=provenance,
                polarity=1,
                importance=mem.importance,
                retrieval_count=mem.retrieval_count,
            )

        if mem.confidence >= 0.85 and mem.type != MemoryType.FACT:
            mem.type = MemoryType.FACT
            logger.info(f"[PW-EBR/UMF-EDR] Memory promoted to FACT: ID {mem.id} (Confidence: {mem.confidence})")
        elif mem.confidence < 0.50 and mem.type == MemoryType.OBSERVATION:
            mem.type = MemoryType.HYPOTHESIS

        mem.last_confirmed_at = now
        db.commit()
        db.refresh(mem)
        return mem

    def record_retrieval(self, db: Session, memory_id: int) -> UserMemoryV2 | None:
        """
        UMF-EDR Closed-Loop Retrieval Plasticity (Testing / Spacing Effect):
        Reinforces memory stability when accessed during task execution.
        """
        mem = db.query(UserMemoryV2).filter(UserMemoryV2.id == memory_id).first()
        if not mem:
            return None
        mem.retrieval_count += 1
        # Plasticity bonus: reinforces confidence and slows future decay
        mem.confidence = min(0.99, mem.confidence + (0.02 * mem.importance))
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

    def get_relevant_structured_memories(
        self, db: Session, category: str | None = None, limit: int = 20
    ) -> list[UserMemoryV2]:
        q = db.query(UserMemoryV2).filter(UserMemoryV2.status == MemoryStatus.ACTIVE)
        if category:
            q = q.filter(UserMemoryV2.category == category)
        return q.order_by(desc(UserMemoryV2.updated_at)).limit(limit).all()

    def resolve_conflicts(self, db: Session, category: str) -> UserMemoryV2 | None:
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
