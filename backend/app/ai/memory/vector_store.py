import uuid
import asyncio
from typing import Optional
from app.database.chromadb_client import get_or_create_collection
from app.ai.memory.embeddings import embed_text, embed_texts
from app.core.logger import logger


class VectorStore:
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._collection = None

    async def _get_collection(self):
        if self._collection is None:
            self._collection = await get_or_create_collection(self.collection_name)
        return self._collection

    async def add(
        self,
        text: str,
        metadata: dict = None,
        doc_id: Optional[str] = None,
    ) -> str:
        collection = await self._get_collection()
        doc_id = doc_id or str(uuid.uuid4())
        embedding = embed_text(text)
        await asyncio.to_thread(
            collection.add,
            ids=[doc_id],
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata or {}],
        )
        return doc_id

    async def add_batch(
        self,
        texts: list[str],
        metadatas: list[dict] = None,
        ids: list[str] = None,
    ) -> list[str]:
        collection = await self._get_collection()
        ids = ids or [str(uuid.uuid4()) for _ in texts]
        embeddings = embed_texts(texts)
        await asyncio.to_thread(
            collection.add,
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{} for _ in texts],
        )
        return ids

    async def search(
        self,
        query: str,
        n_results: int = 5,
        where: dict = None,
    ) -> list[dict]:
        collection = await self._get_collection()
        query_embedding = embed_text(query)
        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where
        try:
            results = await asyncio.to_thread(collection.query, **kwargs)
            items = []
            for i in range(len(results["ids"][0])):
                items.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],
                })
            return items
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    async def delete(self, doc_id: str) -> bool:
        collection = await self._get_collection()
        try:
            await asyncio.to_thread(collection.delete, ids=[doc_id])
            return True
        except Exception as e:
            logger.error(f"Vector delete error: {e}")
            return False

    async def count(self) -> int:
        collection = await self._get_collection()
        return await asyncio.to_thread(collection.count)
