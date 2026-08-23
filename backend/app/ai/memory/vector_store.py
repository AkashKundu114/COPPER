from typing import Any

from app.core.logger import logger

class VectorStore:
    def __init__(self, collection_name: str = "copper_default"):
        self.collection_name = collection_name
        self.collection = None
        try:
            from pathlib import Path

            import chromadb

            db_path = Path(__file__).parent.parent.parent.parent / "data" / "chroma"
            db_path.mkdir(parents=True, exist_ok=True)

            client = chromadb.PersistentClient(path=str(db_path))
            self.collection = client.get_or_create_collection(collection_name)
        except Exception as e:
            logger.warning(f"ChromaDB collection '{collection_name}' fallback active: {e}")

    async def add(self, text: str, metadata: dict[str, Any] | None = None) -> str:
        import uuid

        doc_id = str(uuid.uuid4())
        if self.collection:
            try:
                self.collection.add(ids=[doc_id], documents=[text], metadatas=[metadata or {}])
            except Exception as e:
                logger.warning(f"Failed vector add: {e}")
        return doc_id

    async def search(self, query: str, n_results: int = 5, where: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self.collection:
            try:
                kw = {"query_texts": [query], "n_results": n_results}
                if where:
                    kw["where"] = where
                results = self.collection.query(**kw)
                memories = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                    dists = results["distances"][0] if "distances" in results else [0.0] * len(docs)
                    for doc, meta, dist in zip(docs, metas, dists):
                        memories.append({"document": doc, "metadata": meta, "distance": dist})
                return memories
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        return []

    async def count(self) -> int:
        if self.collection:
            try:
                return self.collection.count()
            except Exception:
                pass
        return 0
