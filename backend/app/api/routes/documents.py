from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.core.logger import logger
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["documents"])


class DocumentSearchRequest(BaseModel):
    query: str
    limit: int = 5


@router.get("/supported")
async def get_supported_types():
    """
    Get dictionary of supported document extensions and categories.
    """
    return {
        "supported_extensions": document_service.SUPPORTED_EXTENSIONS,
        "total_supported": len(document_service.SUPPORTED_EXTENSIONS),
    }


@router.post("/parse")
async def parse_document_file(
    file: UploadFile = File(...),
    index_to_memory: bool = Form(True),
):
    """
    Upload and parse a document file (PDF, CSV, JSON, Markdown, Code, etc.).
    Extracts text, calculates statistics, and indexes into vector memory for AI context.
    """
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="Empty document file uploaded")

        parsed = await document_service.parse_document(
            file_bytes=contents,
            filename=file.filename or "uploaded_document",
            index_to_memory=index_to_memory,
        )
        return parsed
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing document {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Document parsing failed: {e}")


@router.post("/search")
async def search_documents(request: DocumentSearchRequest):
    """
    Search vector memory for indexed document chunks matching the query.
    """
    try:
        from app.ai.memory.memory_manager import memory_manager

        results = await memory_manager.search_documents(request.query, limit=request.limit)
        return {
            "query": request.query,
            "results": results,
            "count": len(results),
        }
    except Exception as e:
        logger.error(f"Document search error: {e}")
        raise HTTPException(status_code=500, detail=f"Document search failed: {e}")
