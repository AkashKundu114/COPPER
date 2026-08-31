from typing import Any

from app.ai.memory.memory_manager import memory_manager
from app.ai.tools.registry import tool_registry
from app.core.logger import logger


@tool_registry.tool(
    name="memory_store",
    description="Store a piece of knowledge, observation, user preference, or fact into COPPER's persistent epistemic memory.",
    parameters={
        "type": "object",
        "properties": {
            "content": {"type": "string", "description": "The fact, preference, or knowledge content to store."},
            "memory_type": {
                "type": "string",
                "description": "Category/type of memory, e.g. 'preference', 'fact', 'observation', 'goal' (default 'observation').",
            },
            "confidence": {
                "type": "number",
                "description": "Confidence score from 0.0 to 1.0 (default 0.9).",
            },
        },
        "required": ["content"],
    },
    return_description="Confirmation of stored memory and assigned ID.",
    guardian_level=0,
)
async def memory_store(content: str, memory_type: str = "observation", confidence: float = 0.9) -> dict[str, Any]:
    try:
        doc_id = await memory_manager.save_document(
            content=content,
            source="agent_tool",
            metadata={"type": memory_type, "confidence": confidence},
        )
        return {
            "status": "success",
            "memory_id": doc_id,
            "memory_type": memory_type,
            "confidence": confidence,
            "message": "Fact stored successfully in persistent memory.",
        }
    except Exception as e:
        logger.error(f"memory_store error: {e}")
        return {"status": "error", "error": str(e)}


@tool_registry.tool(
    name="memory_query",
    description="Search and retrieve relevant long-term memories, user preferences, facts, and documents from vector storage.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query or question to retrieve matching memories for."},
            "limit": {"type": "integer", "description": "Maximum number of memory items to return (default 5)."},
        },
        "required": ["query"],
    },
    return_description="List of matching memory items with text content and similarity distance.",
    guardian_level=0,
)
async def memory_query(query: str, limit: int = 5) -> dict[str, Any]:
    try:
        memories = await memory_manager.get_relevant_memories(query, limit=limit)
        docs = await memory_manager.search_documents(query, limit=limit)

        results = []
        for m in memories:
            results.append({
                "source": "chat_memory",
                "content": m.get("content", ""),
                "type": m.get("memory_type", "chat"),
                "score": m.get("distance", 0.0),
            })
        for d in docs:
            results.append({
                "source": "document_store",
                "content": d.get("document", ""),
                "type": d.get("metadata", {}).get("type", "document"),
                "score": d.get("distance", 0.0),
            })

        return {
            "status": "success",
            "query": query,
            "count": len(results),
            "memories": results[:limit],
        }
    except Exception as e:
        logger.error(f"memory_query error: {e}")
        return {"status": "error", "error": str(e), "memories": []}
