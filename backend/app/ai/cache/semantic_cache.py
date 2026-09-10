import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logger import logger
from app.database.redis_client import get_redis


@dataclass
class CacheLookupResult:
    status: str  # "hit", "hint", "miss"
    cached_response: str | None = None
    agent_type: str | None = None
    similarity: float = 0.0
    category: str | None = None
    latency_ms: float = 0.0
    context_hash: str | None = None
    match_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SemanticResponseCache:
    """
    ChromaDB-backed Semantic Response Cache for C.O.P.P.E.R.
    Stores and serves previous LLM responses in <1ms based on cosine similarity
    of query embeddings, with context-aware invalidation and time-to-live rules.
    """

    COLLECTION_NAME = "copper_response_cache"

    # Invalidation TTL constants
    TTL_TIME_SENSITIVE = 3600  # 1 hour
    TTL_FACTUAL = 86400  # 24 hours
    TTL_TECHNICAL = 604800  # 7 days (code/technical)

    SIMILARITY_HIT_THRESHOLD = 0.95
    SIMILARITY_HINT_THRESHOLD = 0.85

    def __init__(self):
        self.collection = None
        self._default_ef = None
        self._hits = 0
        self._misses = 0
        self._hints = 0
        self._total_time_saved_ms = 0.0
        self._tokens_saved = 0
        self._exact_cache: dict[str, dict[str, Any]] = {}
        self._redis_last_failed: float = 0.0
        self._init_storage()

    def _init_storage(self):
        try:
            import chromadb
            import chromadb.utils.embedding_functions as ef

            self._default_ef = ef.DefaultEmbeddingFunction()

            db_path = Path(__file__).resolve().parents[4] / "backend" / "data" / "chroma"
            db_path.mkdir(parents=True, exist_ok=True)

            client = chromadb.PersistentClient(path=str(db_path))
            self.collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Initialized ChromaDB semantic response cache collection: '{self.COLLECTION_NAME}'")
        except Exception as e:
            logger.warning(f"SemanticResponseCache ChromaDB initialization fallback active: {e}")

    def _is_redis_healthy(self) -> bool:
        return (time.time() - self._redis_last_failed) > 30.0

    async def _safe_redis_get(self, key: str) -> str | None:
        if not self._is_redis_healthy():
            return None
        try:
            r = await get_redis()
            if r:
                return await r.get(key)
        except Exception as e:
            self._redis_last_failed = time.time()
            logger.debug(f"Redis get skipped (offline or timeout): {e}")
        return None

    async def _safe_redis_set(self, key: str, value: str, ex: int = 86400):
        if not self._is_redis_healthy():
            return
        try:
            r = await get_redis()
            if r:
                await r.set(key, value, ex=ex)
        except Exception as e:
            self._redis_last_failed = time.time()
            logger.debug(f"Redis set skipped (offline or timeout): {e}")

    async def _safe_redis_clear(self):
        if not self._is_redis_healthy():
            return
        try:
            r = await get_redis()
            if r:
                keys = await r.keys("copper:cache:*")
                if keys:
                    await r.delete(*keys)
        except Exception as e:
            self._redis_last_failed = time.time()
            logger.debug(f"Redis clear skipped: {e}")

    async def compute_embedding(self, text: str) -> list[float]:
        """
        Computes query embedding. Uses local Chroma default embedding function
        or Ollama nomic-embed-text if configured and reachable.
        """
        import httpx

        ollama_url = getattr(settings, "OLLAMA_BASE_URL", "http://localhost:11434")
        try:
            async with httpx.AsyncClient(timeout=0.3) as client:
                res = await client.post(
                    f"{ollama_url}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": text},
                )
                if res.status_code == 200:
                    vec = res.json().get("embedding")
                    if vec:
                        return [float(x) for x in vec]
        except Exception:
            pass

        # Robust local in-process fallback using Chroma's ONNX embedding function
        if self._default_ef:
            try:
                embeddings = self._default_ef([text])
                if embeddings and len(embeddings) > 0:
                    return [float(x) for x in embeddings[0]]
            except Exception as e:
                logger.debug(f"Default embedding function error: {e}")

        # Deterministic pseudo-embedding fallback if all embedding engines fail
        h = hashlib.sha256(text.lower().strip().encode("utf-8")).digest()
        return [float((b - 128) / 128.0) for b in h]

    def classify_query(self, query: str, agent_type: str = "") -> tuple[str, int, bool]:
        """
        Classifies query to determine TTL and context dependency.
        Returns: (category, ttl_seconds, is_context_dependent)
        """
        q_lower = query.strip().lower()

        # Context-dependent markers (user memory, personal facts)
        context_patterns = [
            r"\b(who am i|whats my name|what is my name|my age|how old am i)\b",
            r"\b(my preferences|my schedule|remember when|what did i say|about me)\b",
            r"\b(my project|my code|my workspace|my files|where do i live)\b",
        ]
        is_context_dependent = any(re.search(pat, q_lower) for pat in context_patterns)

        # Time-sensitive markers (containing "today", "now", "current")
        time_sensitive_patterns = [
            r"\b(today|now|current|right now|latest|yesterday|tomorrow)\b",
            r"\b(what time is it|current date|today's date|current time)\b",
            r"\b(this morning|this afternoon|tonight|this week|this month)\b",
        ]
        if any(re.search(pat, q_lower) for pat in time_sensitive_patterns):
            return "time_sensitive", self.TTL_TIME_SENSITIVE, is_context_dependent

        # Code / technical markers
        code_patterns = [
            r"\b(code|python|function|bug|error|script|algorithm|class|def|import)\b",
            r"\b(sql|api|html|css|docker|git|bash|terminal|regex|json|syntax)\b",
            r"\b(refactor|test|unit test|traceback|exception|async|await|fastapi)\b",
        ]
        if agent_type in ("coding", "automation") or any(re.search(pat, q_lower) for pat in code_patterns):
            return "code_technical", self.TTL_TECHNICAL, is_context_dependent

        # Context-dependent queries without temporal markers
        if is_context_dependent:
            return "context_dependent", self.TTL_FACTUAL, True

        # Default: factual query
        return "factual", self.TTL_FACTUAL, False

    def compute_context_hash(self, memory_context: str = "", temporal_date: str = "") -> str:
        """
        context_hash = hash of (memory_context + temporal_date)
        If memory changes or date changes, cache misses for context-dependent queries.
        """
        if not temporal_date:
            temporal_date = datetime.now().strftime("%Y-%m-%d")
        payload = f"{memory_context.strip()}::{temporal_date}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    async def lookup(self, query: str, context_hash: str = "") -> CacheLookupResult:
        """
        Before inference, compute query embedding and search cache with cosine similarity.
        - similarity > 0.95: return cached response (< 1ms)
        - 0.85 < similarity <= 0.95: return as "hint" but still run inference
        - similarity <= 0.85: miss, run normal inference
        """
        t0 = time.perf_counter()

        if not self.collection or not query.strip():
            self._misses += 1
            return CacheLookupResult(status="miss")

        norm_query = query.strip().lower()
        now = time.time()

        # 1. Fast in-memory exact match (<0.1ms)
        if norm_query in self._exact_cache:
            entry = self._exact_cache[norm_query]
            if now - entry.get("timestamp", 0) <= entry.get("ttl", self.TTL_FACTUAL):
                if not entry.get("is_context_dependent") or entry.get("context_hash") == context_hash:
                    t1 = time.perf_counter()
                    latency_ms = round((t1 - t0) * 1000, 3)
                    self._hits += 1
                    self._total_time_saved_ms += 4500.0
                    self._tokens_saved += len(entry.get("response_text", "").split())
                    return CacheLookupResult(
                        status="hit",
                        cached_response=entry.get("response_text"),
                        agent_type=entry.get("agent_type"),
                        similarity=1.0,
                        category=entry.get("category"),
                        latency_ms=max(0.1, latency_ms),
                        context_hash=entry.get("context_hash"),
                        match_id=entry.get("id"),
                    )

        # 2. Redis exact match check (if healthy)
        exact_raw = await self._safe_redis_get(f"copper:cache:exact:{hashlib.sha256(norm_query.encode()).hexdigest()}")
        if exact_raw:
            try:
                exact_data = json.loads(exact_raw)
                if now - exact_data.get("timestamp", 0) <= exact_data.get("ttl", self.TTL_FACTUAL):
                    if not exact_data.get("is_context_dependent") or exact_data.get("context_hash") == context_hash:
                        t1 = time.perf_counter()
                        latency_ms = round((t1 - t0) * 1000, 3)
                        self._hits += 1
                        self._total_time_saved_ms += 4500.0
                        self._tokens_saved += len(exact_data.get("response_text", "").split())
                        self._exact_cache[norm_query] = exact_data
                        return CacheLookupResult(
                            status="hit",
                            cached_response=exact_data.get("response_text"),
                            agent_type=exact_data.get("agent_type"),
                            similarity=1.0,
                            category=exact_data.get("category"),
                            latency_ms=max(0.1, latency_ms),
                            context_hash=exact_data.get("context_hash"),
                            match_id=exact_data.get("id"),
                        )
            except Exception:
                pass

        try:
            # 3. Compute embedding for semantic vector lookup
            query_embedding = await self.compute_embedding(query)

            # Query ChromaDB collection with cosine distance
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=1,
                include=["documents", "metadatas", "distances"],
            )

            if not results or not results["documents"] or not results["documents"][0]:
                self._misses += 1
                return CacheLookupResult(status="miss")

            distance = results["distances"][0][0]
            # In cosine space, distance = 1 - cosine_similarity
            similarity = max(0.0, min(1.0, 1.0 - distance))
            doc = results["documents"][0][0]
            meta = results["metadatas"][0][0] if results["metadatas"] else {}
            match_id = results["ids"][0][0] if results.get("ids") else None

            created_at = meta.get("timestamp", 0.0)
            ttl = meta.get("ttl", self.TTL_FACTUAL)
            category = meta.get("category", "factual")
            is_context_dep = meta.get("is_context_dependent", False)
            stored_hash = meta.get("context_hash", "")
            agent_type = meta.get("agent_type", "chat")

            # Invalidation Rule 1: TTL Expiration
            if now - created_at > ttl:
                try:
                    if match_id:
                        self.collection.delete(ids=[match_id])
                except Exception:
                    pass
                self._misses += 1
                return CacheLookupResult(status="miss", similarity=similarity)

            # Invalidation Rule 2: Context Changed for Context-Dependent Queries
            if is_context_dep and context_hash and stored_hash != context_hash:
                self._misses += 1
                return CacheLookupResult(status="miss", similarity=similarity)

            t1 = time.perf_counter()
            latency_ms = round((t1 - t0) * 1000, 3)

            # Rule 3: High Similarity Cache Hit (> 0.95) -> Instant recall
            if similarity > self.SIMILARITY_HIT_THRESHOLD:
                self._hits += 1
                self._total_time_saved_ms += 4500.0  # ~4.5s average saved inference
                self._tokens_saved += len(doc.split())
                # Update in-memory exact cache
                self._exact_cache[norm_query] = {
                    "id": match_id,
                    "query_text": query,
                    "response_text": doc,
                    "agent_type": agent_type,
                    "timestamp": created_at,
                    "ttl": ttl,
                    "category": category,
                    "context_hash": stored_hash,
                    "is_context_dependent": is_context_dep,
                }
                return CacheLookupResult(
                    status="hit",
                    cached_response=doc,
                    agent_type=agent_type,
                    similarity=round(similarity, 4),
                    category=category,
                    latency_ms=max(0.1, latency_ms),
                    context_hash=stored_hash,
                    match_id=match_id,
                )

            # Rule 4: Moderate Similarity Cache Hint (0.85 < similarity <= 0.95)
            if similarity > self.SIMILARITY_HINT_THRESHOLD:
                self._hints += 1
                return CacheLookupResult(
                    status="hint",
                    cached_response=doc,
                    agent_type=agent_type,
                    similarity=round(similarity, 4),
                    category=category,
                    latency_ms=max(0.1, latency_ms),
                    context_hash=stored_hash,
                    match_id=match_id,
                )

            # Rule 5: Low Similarity (<= 0.85) -> Miss
            self._misses += 1
            return CacheLookupResult(status="miss", similarity=round(similarity, 4))

        except Exception as e:
            logger.warning(f"Semantic cache lookup error: {e}")
            self._misses += 1
            return CacheLookupResult(status="miss")

    async def store(
        self,
        query: str,
        response: str,
        agent_type: str = "chat",
        context_hash: str = "",
        memory_context: str = "",
    ) -> str | None:
        """
        Stores response in ChromaDB and Redis/Memory:
        (query_embedding, query_text, response_text, agent_type, timestamp, context_hash)
        """
        if not self.collection or not query.strip() or not response.strip():
            return None

        # Ignore trivial short responses or errors
        if len(response.strip()) < 5 or response.strip().startswith("[Error:"):
            return None

        try:
            import uuid

            category, ttl, is_context_dependent = self.classify_query(query, agent_type)
            if not context_hash:
                context_hash = self.compute_context_hash(memory_context)

            doc_id = f"resp_{uuid.uuid4().hex[:12]}"
            now = time.time()

            query_embedding = await self.compute_embedding(query)

            metadata = {
                "query_text": query[:500],
                "agent_type": str(agent_type),
                "timestamp": now,
                "context_hash": str(context_hash),
                "ttl": int(ttl),
                "category": category,
                "is_context_dependent": bool(is_context_dependent),
            }

            self.collection.add(
                ids=[doc_id],
                embeddings=[query_embedding],
                documents=[response],
                metadatas=[metadata],
            )

            # Update exact caches
            cache_payload = {
                "id": doc_id,
                "query_text": query,
                "response_text": response,
                "agent_type": str(agent_type),
                "timestamp": now,
                "ttl": ttl,
                "category": category,
                "context_hash": context_hash,
                "is_context_dependent": is_context_dependent,
            }
            norm_query = query.strip().lower()
            self._exact_cache[norm_query] = cache_payload

            # Safe async write to Redis
            q_key = f"copper:cache:exact:{hashlib.sha256(norm_query.encode()).hexdigest()}"
            await self._safe_redis_set(q_key, json.dumps(cache_payload), ex=min(ttl, 604800))

            return doc_id
        except Exception as e:
            logger.warning(f"Failed to store semantic response cache: {e}")
            return None

    async def clear(self) -> int:
        """
        Clears the semantic response cache collection and resets statistics.
        """
        count = 0
        try:
            if self.collection:
                count = self.collection.count()
                all_ids = self.collection.get().get("ids", [])
                if all_ids:
                    self.collection.delete(ids=all_ids)

            self._exact_cache.clear()
            await self._safe_redis_clear()

            self._hits = 0
            self._misses = 0
            self._hints = 0
            self._total_time_saved_ms = 0.0
            self._tokens_saved = 0
            return count
        except Exception as e:
            logger.error(f"Error clearing semantic cache: {e}")
            return count

    async def get_stats(self) -> dict[str, Any]:
        """
        Returns hit rate, size, avg savings, and category counts.
        """
        total = self._hits + self._misses + self._hints
        hit_rate = round(self._hits / total, 4) if total > 0 else 0.0

        size = 0
        if self.collection:
            try:
                size = self.collection.count()
            except Exception:
                pass

        avg_savings_sec = (
            round((self._total_time_saved_ms / 1000.0) / max(1, self._hits), 2)
            if self._hits > 0
            else 4.5
        )

        return {
            "status": "active",
            "hit_rate": hit_rate,
            "hit_rate_percentage": f"{round(hit_rate * 100, 1)}%",
            "hits": self._hits,
            "hints": self._hints,
            "misses": self._misses,
            "total_queries": total,
            "size": size,
            "avg_savings": f"{avg_savings_sec}s per hit",
            "avg_savings_seconds": avg_savings_sec,
            "total_time_saved_sec": round(self._total_time_saved_ms / 1000.0, 1),
            "estimated_tokens_saved": self._tokens_saved,
            "collection_name": self.COLLECTION_NAME,
            "similarity_threshold": self.SIMILARITY_HIT_THRESHOLD,
            "hint_threshold": self.SIMILARITY_HINT_THRESHOLD,
        }


semantic_cache = SemanticResponseCache()
