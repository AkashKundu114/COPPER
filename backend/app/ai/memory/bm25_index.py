import re
from typing import Any

from rank_bm25 import BM25Okapi

from app.core.logger import logger


def tokenize_text(text: str) -> list[str]:
    """Lowercase word tokenizer for BM25 indexing."""
    if not text:
        return []
    return re.findall(r"\w+", text.lower())


class BM25Index:
    """
    BM25 Keyword Index using rank_bm25.
    Indexes documents and chat history, auto-updating dynamically as new entries are added.
    """

    def __init__(self, auto_bootstrap: bool = True):
        self._documents: dict[str, dict[str, Any]] = {}
        self._corpus_ids: list[str] = []
        self._corpus_tokens: list[list[str]] = []
        self._bm25: BM25Okapi | None = None
        self._is_dirty: bool = False
        self._auto_bootstrap: bool = auto_bootstrap
        self._initialized: bool = not auto_bootstrap

    def add_document(
        self,
        doc_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        source: str = "document",
    ) -> None:
        """Adds or updates a single document in the BM25 index."""
        if not doc_id or not content:
            return

        tokens = tokenize_text(content)
        self._documents[doc_id] = {
            "id": doc_id,
            "content": content,
            "tokens": tokens,
            "metadata": metadata or {},
            "source": source,
        }
        self._is_dirty = True
        self._rebuild_index()

    def add_documents(self, items: list[dict[str, Any]]) -> None:
        """Batch adds multiple documents to the BM25 index."""
        for item in items:
            doc_id = item.get("id") or item.get("doc_id")
            content = item.get("content") or item.get("text") or item.get("document", "")
            if not doc_id or not content:
                continue
            tokens = tokenize_text(content)
            self._documents[str(doc_id)] = {
                "id": str(doc_id),
                "content": content,
                "tokens": tokens,
                "metadata": item.get("metadata") or {},
                "source": item.get("source", "document"),
            }
        self._is_dirty = True
        self._rebuild_index()

    def remove_document(self, doc_id: str) -> bool:
        """Removes a document from the index by ID."""
        if doc_id in self._documents:
            del self._documents[doc_id]
            self._is_dirty = True
            self._rebuild_index()
            return True
        return False

    def _rebuild_index(self) -> None:
        """Rebuilds the internal BM25Okapi data structures."""
        if not self._documents:
            self._corpus_ids = []
            self._corpus_tokens = []
            self._bm25 = None
            self._is_dirty = False
            return

        self._corpus_ids = list(self._documents.keys())
        self._corpus_tokens = [self._documents[doc_id]["tokens"] for doc_id in self._corpus_ids]

        valid_tokens_exist = any(len(toks) > 0 for toks in self._corpus_tokens)
        if valid_tokens_exist:
            try:
                self._bm25 = BM25Okapi(self._corpus_tokens)
            except Exception as e:
                logger.warning(f"BM25Okapi build failed, will retry on next change: {e}")
                self._bm25 = None
        else:
            self._bm25 = None

        self._is_dirty = False

    def search(self, query: str, limit: int = 10) -> list[tuple[str, float]]:
        """
        Searches the BM25 index with a query string.
        Returns: [(doc_id, bm25_score), ...] ranked in descending score order.
        """
        self._ensure_initialized()

        if self._is_dirty:
            self._rebuild_index()

        if not self._bm25 or not self._corpus_ids:
            return []

        tokens = tokenize_text(query)
        if not tokens:
            return []

        scores = self._bm25.get_scores(tokens)

        # Pair document IDs with positive scores
        results: list[tuple[str, float]] = []
        for doc_id, score in zip(self._corpus_ids, scores):
            score_f = float(score)
            if score_f > 0.0:
                results.append((doc_id, round(score_f, 4)))

        # Fallback to simple token-frequency matching if BM25 gives all zeros
        # (e.g. on 2-document corpus where IDF can evaluate to 0 in standard Okapi formula)
        if not results:
            query_set = set(tokens)
            for doc_id in self._corpus_ids:
                doc_tokens = self._documents[doc_id]["tokens"]
                overlap = sum(1 for t in doc_tokens if t in query_set)
                if overlap > 0:
                    tf_score = round(overlap / max(1, len(doc_tokens)), 4)
                    results.append((doc_id, tf_score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def search_documents(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """
        Returns ranked full document dictionaries matching the BM25 query.
        """
        scored_tuples = self.search(query, limit=limit)
        results = []
        for doc_id, score in scored_tuples:
            doc = self._documents.get(doc_id)
            if doc:
                results.append(
                    {
                        "doc_id": doc_id,
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "source": doc["source"],
                        "bm25_score": score,
                    }
                )
        return results

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        """Retrieves an indexed document by ID."""
        return self._documents.get(doc_id)

    def count(self) -> int:
        """Returns the total number of indexed items."""
        return len(self._documents)

    def clear(self) -> None:
        """Resets the index."""
        self._documents.clear()
        self._corpus_ids.clear()
        self._corpus_tokens.clear()
        self._bm25 = None
        self._is_dirty = False
        self._initialized = True

    def _ensure_initialized(self) -> None:
        """Bootstraps index from existing vector stores if not already done."""
        if self._initialized:
            return
        self._initialized = True
        try:
            self._bootstrap_from_chroma()
        except Exception as e:
            logger.debug(f"BM25 bootstrap skipped: {e}")

    def _bootstrap_from_chroma(self) -> None:
        """Loads documents and chat memories from ChromaDB into BM25 on first start."""
        from app.ai.memory.vector_store import VectorStore
        from app.core.constants import CHROMA_COLLECTION_CHAT

        # 1. Documents store
        doc_store = VectorStore("copper_documents")
        if doc_store.collection:
            try:
                data = doc_store.collection.get()
                if data and "ids" in data and data["ids"]:
                    ids = data["ids"]
                    docs = data.get("documents") or []
                    metas = data.get("metadatas") or [{}] * len(ids)
                    for d_id, content, meta in zip(ids, docs, metas):
                        if content:
                            tokens = tokenize_text(content)
                            self._documents[d_id] = {
                                "id": d_id,
                                "content": content,
                                "tokens": tokens,
                                "metadata": meta or {},
                                "source": "document",
                            }
            except Exception as e:
                logger.debug(f"Could not bootstrap documents into BM25: {e}")

        # 2. Chat memories store
        chat_store = VectorStore(CHROMA_COLLECTION_CHAT)
        if chat_store.collection:
            try:
                cdata = chat_store.collection.get()
                if cdata and "ids" in cdata and cdata["ids"]:
                    c_ids = cdata["ids"]
                    c_docs = cdata.get("documents") or []
                    c_metas = cdata.get("metadatas") or [{}] * len(c_ids)
                    for c_id, content, meta in zip(c_ids, c_docs, c_metas):
                        if content:
                            tokens = tokenize_text(content)
                            self._documents[c_id] = {
                                "id": c_id,
                                "content": content,
                                "tokens": tokens,
                                "metadata": meta or {},
                                "source": "chat",
                            }
            except Exception as e:
                logger.debug(f"Could not bootstrap chat memories into BM25: {e}")

        if self._documents:
            self._rebuild_index()
            logger.info(f"BM25Index bootstrapped with {len(self._documents)} items from vector stores")


bm25_index = BM25Index()
