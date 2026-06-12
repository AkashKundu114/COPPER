from typing import Any, Optional
import chromadb
from app.core.config import settings
from app.core.logger import logger

_client: Optional[Any] = None


async def get_chroma_client() -> Any:
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.CHROMA_HOST,
            port=settings.CHROMA_PORT,
        )
        logger.info("ChromaDB client connected")
    return _client


async def get_or_create_collection(name: str, metadata: dict = None):
    client = await get_chroma_client()
    try:
        collection = client.get_or_create_collection(
            name=name,
            metadata=metadata or {"hnsw:space": "cosine"},
        )
        return collection
    except Exception as e:
        logger.error(f"ChromaDB collection error: {e}")
        raise
