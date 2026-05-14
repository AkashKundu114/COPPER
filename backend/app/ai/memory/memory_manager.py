from typing import Optional
from app.ai.memory.vector_store import VectorStore
from app.core.constants import CHROMA_COLLECTION_CHAT, MEMORY_SEARCH_LIMIT
from app.core.logger import logger

chat_store = VectorStore(CHROMA_COLLECTION_CHAT)
doc_store = VectorStore("copper_documents")


class MemoryManager:
    def __init__(self):
        self.chat_store = chat_store
        self.doc_store = doc_store

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


memory_manager = MemoryManager()
