from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from app.services.memory_service import memory_service
from app.database.postgres import get_db
from app.core.logger import logger

router = APIRouter(prefix="/memory", tags=["memory"])


class MemoryCreate(BaseModel):
    key: str
    content: str
    source: str = "manual"
    metadata: Optional[dict] = None


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


@router.post("/search")
async def search_memory(req: SearchRequest):
    try:
        results = await memory_service.search(req.query, req.limit)
        return results
    except Exception as e:
        logger.error(f"Memory search error: {e}")
        raise HTTPException(status_code=500, detail="Memory search failed")


@router.post("/add")
async def add_memory(req: MemoryCreate, db: Session = Depends(get_db)):
    try:
        result = await memory_service.add_memory(
            req.key, req.content, req.source, req.metadata, db
        )
        return result
    except Exception as e:
        logger.error(f"Add memory error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add memory")


@router.get("/all")
async def get_memories(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    return memory_service.get_all_memories(db, skip, limit)


@router.delete("/{memory_id}")
async def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    success = memory_service.delete_memory(db, memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True}


@router.get("/stats")
async def get_stats():
    return await memory_service.get_stats()


@router.post("/ingest")
async def ingest_document(
    file: UploadFile = File(...),
    source: Optional[str] = None,
):
    try:
        content = await file.read()
        source = source or file.filename
        text = content.decode("utf-8", errors="ignore")
        count = await memory_service.ingest_text(text, source)
        return {"chunks_ingested": count, "source": source}
    except Exception as e:
        logger.error(f"Ingest error: {e}")
        raise HTTPException(status_code=500, detail="Ingestion failed")
