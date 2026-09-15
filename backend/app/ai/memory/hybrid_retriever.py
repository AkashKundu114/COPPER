"""
Symbol-Preserving Hybrid RRF Retriever & Query Intent Classifier.

Information Retrieval (IR) & Search Engine Concepts:
1. Lexical vs Semantic Trade-off: Dense vector embeddings excel at semantic paraphrasing
   but suffer from catastrophic recall degradation on exact technical identifiers (e.g.,
   `get_active_session_token()`, `0x80070005`, `alembic_version`).
2. Symbol-Preserving Tokenizer: Emits compound programming tokens (camelCase, snake_case,
   dotted namespaces) as single indexed entities alongside sub-word n-grams.
3. Dynamic Intent Classification: Automatically adjusts Reciprocal Rank Fusion (RRF)
   weights based on syntactic query structure.
4. Reciprocal Rank Fusion (RRF):
   RRF_Score(d) = w_dense * (1 / (k + rank_dense(d))) + w_lexical * (1 / (k + rank_lexical(d)))
"""

import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.ai.memory.bm25_index import bm25_index
from app.ai.memory.vector_store import VectorStore
from app.core.logger import logger

RRF_K_DEFAULT: int = 60


class QueryIntent(str, Enum):
    CODE_SYMBOL = "CODE_SYMBOL"
    SEMANTIC = "SEMANTIC"
    BALANCED = "BALANCED"


# Code patterns to identify exact technical identifiers
CODE_SYMBOL_PATTERNS = [
    re.compile(r"\b[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z0-9_]+\b"),  # dotted path (os.path.join)
    re.compile(r"\b[a-z]+(?:_[a-z0-9]+)+\b"),  # snake_case
    re.compile(r"\b[a-z]+(?:[A-Z][a-z0-9]+)+\b"),  # camelCase
    re.compile(r"\b[A-Z]+(?:_[A-Z0-9]+)+\b"),  # SCREAMING_SNAKE
    re.compile(r"\b0x[0-9a-fA-F]+\b"),  # hex code
    re.compile(r"\b\w+\.(?:py|json|ts|tsx|js|html|css|yaml|yml|md|sql)\b"),  # filename
    re.compile(r"\b(?:def|class|function|import|export|SELECT|FROM|WHERE)\b"),  # code keywords
]


class SymbolPreservingTokenizer:
    """
    Tokenizes text while preserving programmatic identifiers as unified tokens.
    """

    @staticmethod
    def tokenize(text: str) -> list[str]:
        # Extract preserved exact symbols
        symbols = set()
        for pat in CODE_SYMBOL_PATTERNS:
            for match in pat.finditer(text):
                symbols.add(match.group(0).lower())

        # Standard tokenization
        standard_tokens = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())

        # Combine with compound symbols having higher priority
        combined = list(symbols) + [t for t in standard_tokens if t not in symbols]
        return combined


class HybridRRFRetriever:
    def __init__(self, doc_store: VectorStore | None = None, rrf_k: int = RRF_K_DEFAULT):
        self.doc_store = doc_store or VectorStore("copper_documents")
        self.rrf_k = rrf_k
        self.tokenizer = SymbolPreservingTokenizer()

    def classify_intent(self, query: str) -> tuple[QueryIntent, float, float]:
        """
        Classifies query into CODE_SYMBOL, SEMANTIC, or BALANCED.
        Returns (intent, w_dense, w_lexical).
        """
        code_matches = sum(len(pat.findall(query)) for pat in CODE_SYMBOL_PATTERNS)
        words = query.strip().split()

        # If significant portion is code symbols or exact filename
        if code_matches >= 1 and len(words) <= 5:
            # Code/symbol query: heavy lexical priority
            return QueryIntent.CODE_SYMBOL, 0.25, 0.75
        elif code_matches >= 2:
            return QueryIntent.CODE_SYMBOL, 0.35, 0.65
        elif len(words) >= 6 and "?" in query:
            # Conversational/question query: heavy semantic priority
            return QueryIntent.SEMANTIC, 0.75, 0.25
        else:
            # Balanced
            return QueryIntent.BALANCED, 0.50, 0.50

    async def search(
        self,
        query: str,
        limit: int = 10,
        candidate_multiplier: int = 3,
        source_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Executes Symbol-Preserving Hybrid RRF Search.
        """
        intent, w_dense, w_lexical = self.classify_intent(query)
        fetch_k = max(limit * candidate_multiplier, 15)

        # 1. Dense Semantic Vector Search
        vector_results: list[dict[str, Any]] = []
        try:
            vector_results = await self.doc_store.search(query, n_results=fetch_k)
        except Exception as e:
            logger.debug(f"[HybridRRF] Vector search failed: {e}")

        # 2. Symbol-Preserved Lexical BM25 Search
        bm25_results: list[dict[str, Any]] = []
        try:
            bm25_results = bm25_index.search_documents(query, limit=fetch_k)
        except Exception as e:
            logger.debug(f"[HybridRRF] BM25 search failed: {e}")

        candidates: dict[str, dict[str, Any]] = {}

        # Process Dense Candidates
        for rank, item in enumerate(vector_results, start=1):
            doc_text = item.get("document", "").strip()
            if not doc_text:
                continue

            meta = item.get("metadata") or {}
            doc_id = str(meta.get("id") or meta.get("doc_id") or f"vec_{hash(doc_text)}")
            dist = float(item.get("distance", 1.0))
            dense_rrf = w_dense * (1.0 / (self.rrf_k + rank))

            candidates[doc_text] = {
                "doc_id": doc_id,
                "content": doc_text,
                "metadata": meta,
                "source": meta.get("source", "document"),
                "dense_rank": rank,
                "lexical_rank": None,
                "vector_distance": round(dist, 4),
                "bm25_score": 0.0,
                "rrf_score": dense_rrf,
                "detected_intent": intent.value,
            }

        # Process Lexical BM25 Candidates
        for rank, b_item in enumerate(bm25_results, start=1):
            doc_text = b_item.get("content", "").strip()
            if not doc_text:
                continue

            bm25_score = float(b_item.get("bm25_score", 0.0))
            b_meta = b_item.get("metadata") or {}
            b_id = str(b_item.get("doc_id") or b_meta.get("id") or f"bm25_{hash(doc_text)}")
            b_source = b_item.get("source", "document")
            lexical_rrf = w_lexical * (1.0 / (self.rrf_k + rank))

            if doc_text in candidates:
                candidates[doc_text]["lexical_rank"] = rank
                candidates[doc_text]["bm25_score"] = bm25_score
                candidates[doc_text]["rrf_score"] += lexical_rrf
                if not candidates[doc_text]["metadata"] and b_meta:
                    candidates[doc_text]["metadata"] = b_meta
            else:
                candidates[doc_text] = {
                    "doc_id": b_id,
                    "content": doc_text,
                    "metadata": b_meta,
                    "source": b_source,
                    "dense_rank": None,
                    "lexical_rank": rank,
                    "vector_distance": None,
                    "bm25_score": bm25_score,
                    "rrf_score": lexical_rrf,
                    "detected_intent": intent.value,
                }

        merged = list(candidates.values())
        if source_filter:
            merged = [c for c in merged if c.get("source") == source_filter]

        # Sort descending by composite RRF score
        merged.sort(key=lambda x: x["rrf_score"], reverse=True)

        for c in merged:
            c["rrf_score"] = round(c["rrf_score"], 6)

        return merged[:limit]


hybrid_retriever = HybridRRFRetriever()
