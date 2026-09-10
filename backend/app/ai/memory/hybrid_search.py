from typing import Any

from app.ai.memory.bm25_index import bm25_index
from app.ai.memory.vector_store import VectorStore
from app.core.logger import logger

RRF_K_DEFAULT: int = 60


class HybridSearch:
    """
    Hybrid Search combining ChromaDB vector semantic retrieval and BM25 keyword matching
    fused using Reciprocal Rank Fusion (RRF):
        RRF_score(d) = sum(1 / (k + rank_i(d)))
    """

    def __init__(self, doc_store: VectorStore | None = None, rrf_k: int = RRF_K_DEFAULT):
        self.doc_store = doc_store or VectorStore("copper_documents")
        self.rrf_k = rrf_k

    async def search(
        self,
        query: str,
        limit: int = 10,
        candidate_multiplier: int = 2,
        rrf_k: int | None = None,
        source_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Executes hybrid retrieval:
        1. Query ChromaDB vector store for top candidates.
        2. Query BM25 index for top keyword candidates.
        3. Fuse both candidate lists using Reciprocal Rank Fusion with constant k (default 60).
        4. Deduplicate and return top `limit` merged candidates.
        """
        k_val = rrf_k if rrf_k is not None else self.rrf_k
        fetch_k = max(limit * candidate_multiplier, 15)

        # 1. Vector Search
        vector_results: list[dict[str, Any]] = []
        try:
            vector_results = await self.doc_store.search(query, n_results=fetch_k)
        except Exception as e:
            logger.warning(f"Vector search branch in HybridSearch failed: {e}")

        # 2. BM25 Search
        bm25_results: list[dict[str, Any]] = []
        try:
            bm25_results = bm25_index.search_documents(query, limit=fetch_k)
        except Exception as e:
            logger.warning(f"BM25 search branch in HybridSearch failed: {e}")

        # 3. Reciprocal Rank Fusion
        candidates: dict[str, dict[str, Any]] = {}

        # Process Vector candidates (rank starts at 1)
        for rank, item in enumerate(vector_results, start=1):
            doc_text = item.get("document", "").strip()
            if not doc_text:
                continue

            meta = item.get("metadata") or {}
            doc_id = str(meta.get("id") or meta.get("doc_id") or f"vec_{hash(doc_text)}")
            key = doc_text.strip()

            dist = float(item.get("distance", 1.0))
            # Normalized vector similarity score from distance
            vec_sim = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

            candidates[key] = {
                "doc_id": doc_id,
                "content": doc_text,
                "metadata": meta,
                "source": meta.get("source", "document"),
                "vector_rank": rank,
                "bm25_rank": None,
                "vector_distance": round(dist, 4),
                "vector_similarity": round(vec_sim, 4),
                "bm25_score": 0.0,
                "rrf_score": 1.0 / (k_val + rank),
            }

        # Process BM25 candidates
        for rank, b_item in enumerate(bm25_results, start=1):
            doc_text = b_item.get("content", "").strip()
            if not doc_text:
                continue

            key = doc_text.strip()
            bm25_score = float(b_item.get("bm25_score", 0.0))
            b_meta = b_item.get("metadata") or {}
            b_id = str(b_item.get("doc_id") or b_meta.get("id") or f"bm25_{hash(doc_text)}")
            b_source = b_item.get("source", "document")

            if key in candidates:
                candidates[key]["bm25_rank"] = rank
                candidates[key]["bm25_score"] = bm25_score
                candidates[key]["rrf_score"] += 1.0 / (k_val + rank)
                if not candidates[key]["metadata"] and b_meta:
                    candidates[key]["metadata"] = b_meta
            else:
                candidates[key] = {
                    "doc_id": b_id,
                    "content": doc_text,
                    "metadata": b_meta,
                    "source": b_source,
                    "vector_rank": None,
                    "bm25_rank": rank,
                    "vector_distance": None,
                    "vector_similarity": 0.0,
                    "bm25_score": bm25_score,
                    "rrf_score": 1.0 / (k_val + rank),
                }

        # Filter by source if requested
        merged = list(candidates.values())
        if source_filter:
            merged = [c for c in merged if c.get("source") == source_filter]

        # Sort descending by RRF score
        merged.sort(key=lambda x: x["rrf_score"], reverse=True)

        for item in merged:
            item["rrf_score"] = round(item["rrf_score"], 6)

        return merged[:limit]


hybrid_search = HybridSearch()
