from typing import Optional
from sqlalchemy.orm import Session
from app.ai.memory.memory_manager import memory_manager
from app.database.models.memory import Memory
from app.core.logger import logger


class MemoryService:
    async def search(self, query: str, limit: int = 10) -> list[dict]:
        results = await memory_manager.search_relevant_context(query, limit=limit)
        doc_results = await memory_manager.search_documents(query, limit=5)
        return {
            "chat_context": results,
            "documents": doc_results,
        }

    async def add_memory(
        self,
        key: str,
        content: str,
        source: str = "manual",
        metadata: dict = None,
        db: Optional[Session] = None,
    ) -> dict:
        doc_id = await memory_manager.save_document(content, source, metadata)

        if db:
            mem = Memory(key=key, content=content, source=source, extra_metadata=metadata)
            db.add(mem)
            db.commit()
            db.refresh(mem)
            return mem.to_dict()

        return {"key": key, "vector_id": doc_id, "source": source}

    def get_all_memories(self, db: Session, skip: int = 0, limit: int = 50) -> list[dict]:
        memories = db.query(Memory).offset(skip).limit(limit).all()
        return [m.to_dict() for m in memories]

    def delete_memory(self, db: Session, memory_id: int) -> bool:
        mem = db.query(Memory).filter(Memory.id == memory_id).first()
        if not mem:
            return False
        db.delete(mem)
        db.commit()
        return True

    async def get_stats(self) -> dict:
        return await memory_manager.get_memory_stats()

    async def ingest_text(self, content: str, source: str, chunk_size: int = 1000) -> int:
        """Ingest long text by splitting into chunks."""
        chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        ids = await memory_manager.doc_store.add_batch(
            texts=chunks,
            metadatas=[{"source": source, "chunk": i} for i in range(len(chunks))],
        )
        logger.info(f"Ingested {len(ids)} chunks from '{source}'")
        return len(ids)


memory_service = MemoryService()
