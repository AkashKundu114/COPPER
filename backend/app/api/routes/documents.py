from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.core.logger import logger
from app.services.document_service import document_service

router = APIRouter(prefix="/documents", tags=["documents"])

MIME_MAP = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "txt": "text/plain",
    "md": "text/markdown",
    "html": "text/html",
    "csv": "text/csv",
    "tsv": "text/tab-separated-values",
    "json": "application/json",
    "yaml": "text/yaml",
    "yml": "text/yaml",
}


class DocumentSearchRequest(BaseModel):
    query: str
    limit: int = 5


class DocumentGenerateRequest(BaseModel):
    title: str
    format: str = "pdf"
    prompt: str | None = None
    template_type: str = "general"
    sections: list[dict[str, Any]] | None = None
    headers: list[str] | None = None
    rows: list[list[Any]] | None = None
    data: Any | None = None
    author: str = "C.O.P.P.E.R. AI"
    index_to_memory: bool = True


@router.get("/supported")
async def get_supported_types():
    """
    Get dictionary of supported document extensions and categories.
    """
    return {
        "supported_extensions": document_service.SUPPORTED_EXTENSIONS,
        "total_supported": len(document_service.SUPPORTED_EXTENSIONS),
    }


@router.get("/templates")
async def get_document_templates():
    """
    Get list of pre-configured document archetype templates and recommendations.
    """
    return {
        "templates": document_service.DOCUMENT_TEMPLATES,
        "total_templates": len(document_service.DOCUMENT_TEMPLATES),
    }


@router.get("/generated")
async def list_generated_documents():
    """
    List all documents generated and stored in the documents repository.
    """
    try:
        docs = document_service.list_generated_documents()
        return {
            "documents": docs,
            "total": len(docs),
        }
    except Exception as e:
        logger.error(f"Error listing generated documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate")
async def generate_document(req: DocumentGenerateRequest):
    """
    Autonomous Document Generation Endpoint:
    Creates PDF, Word (DOCX), Markdown, HTML, CSV/TSV, or JSON documents.
    """
    try:
        # If a natural language prompt was provided without manual sections, use DocumentAgent
        if req.prompt and not req.sections:
            from app.ai.agents.document_agent import document_agent

            prompt_full = f"Format: {req.format}. Title: {req.title}. Template: {req.template_type}.\n\nRequirements:\n{req.prompt}"
            agent_result = await document_agent.run(
                message=prompt_full,
                history=[],
                memory_context="",
            )
            # Find the most recently created document
            docs = document_service.list_generated_documents()
            latest = docs[0] if docs else None
            return {
                "status": "success",
                "message": agent_result,
                "document": latest,
            }

        # Otherwise create directly from structured section parameters
        doc_meta = await document_service.create_document(
            format=req.format,
            title=req.title,
            sections=req.sections,
            headers=req.headers,
            rows=req.rows,
            data=req.data,
            template_type=req.template_type,
            author=req.author,
            index_to_memory=req.index_to_memory,
        )
        return {
            "status": "success",
            "document": doc_meta,
        }

    except Exception as e:
        logger.error(f"Failed to generate document: {e}")
        raise HTTPException(status_code=500, detail=f"Document generation failed: {e}")


@router.get("/download/{filename}")
async def download_document(filename: str):
    """
    Download a generated document artifact with proper headers and MIME type.
    """
    file_path = document_service.get_document_file_path(filename)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="Requested document not found")

    ext = file_path.suffix.lstrip(".").lower()
    media_type = MIME_MAP.get(ext, "application/octet-stream")

    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=file_path.name,
    )


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

