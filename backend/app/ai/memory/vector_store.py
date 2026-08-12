from typing import List, Dict, Any
from app.core.logger import logger

try:
    import chromadb
    client = chromadb.Client()
    epistemic_collection = client.get_or_create_collection("copper_epistemic_memory")
except Exception as e:
    logger.warning(f"ChromaDB local vector store fallback: {e}")
    client = None
    epistemic_collection = None


class VectorStore:
    def add_memory(self, memory_id: str, content: str, metadata: Dict[str, Any]):
        if epistemic_collection:
            try:
                epistemic_collection.add(
                    ids=[memory_id],
                    documents=[content],
                    metadatas=[metadata]
                )
            except Exception as e:
                logger.warning(f"Failed to add vector memory: {e}")

    def query_memory(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if epistemic_collection:
            try:
                results = epistemic_collection.query(
                    query_texts=[query],
                    n_results=top_k
                )
                memories = []
                if results and "documents" in results and results["documents"]:
                    docs = results["documents"][0]
                    metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                    for doc, meta in zip(docs, metas):
                        memories.append({"content": doc, **meta})
                return memories
            except Exception as e:
                logger.warning(f"Vector search failed: {e}")
        return []


vector_store = VectorStore()
