from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.ai.knowledge.entity_extractor import entity_extractor
from app.ai.knowledge.graph_store import graph_store

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class EntityCreateRequest(BaseModel):
    name: str = Field(..., description="Entity name")
    type: str = Field("CONCEPT", description="Entity type: PERSON, PROJECT, TECHNOLOGY, etc.")
    confidence: float = Field(0.8, ge=0.5, le=1.0, description="Confidence score between 0.5 and 1.0")
    context: str = Field("", description="Descriptive context or snippet")
    metadata: dict[str, Any] | None = None


class RelationshipCreateRequest(BaseModel):
    source: str = Field(..., description="Source entity canonical/display name")
    target: str = Field(..., description="Target entity canonical/display name")
    type: str = Field("RELATED_TO", description="Relationship type: WORKS_ON, USES, DEPENDS_ON, etc.")
    confidence: float = Field(0.8, ge=0.5, le=1.0, description="Confidence score between 0.5 and 1.0")
    context: str = Field("", description="Descriptive context or snippet")
    metadata: dict[str, Any] | None = None


class ExtractKnowledgeRequest(BaseModel):
    text: str = Field(..., min_length=3, description="Conversation or document text to extract from")
    session_id: str | None = None


@router.get("/entities")
async def list_entities(
    type: str | None = Query(None, description="Filter by entity type (PERSON, PROJECT, etc.)"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    search: str | None = Query(None, description="Search entity by name substring"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of entities to return"),
    offset: int = Query(0, ge=0, description="Offset pagination"),
):
    """
    List all knowledge graph entities with types, confidence scores, and evidence counts.
    """
    entities = graph_store.list_entities(
        entity_type=type, min_confidence=min_confidence, search=search, limit=limit, offset=offset
    )
    return {"data": entities, "count": len(entities)}


@router.post("/entities")
async def create_entity(req: EntityCreateRequest):
    """
    Manually create or reinforce an entity in the knowledge graph.
    """
    try:
        saved = graph_store.add_entity(
            name=req.name,
            entity_type=req.type,
            confidence=req.confidence,
            context=req.context,
            metadata=req.metadata,
        )
        return {"status": "success", "entity": saved}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/entities/{id_or_name}")
async def get_entity(id_or_name: str):
    """
    Retrieve entity details by integer ID or name.
    """
    entity = graph_store.query_entity(id_or_name)
    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")
    return {"status": "success", "entity": entity}


@router.delete("/entities/{id}")
async def delete_entity(id: int):
    """
    Remove an entity and its connected relationships from the knowledge graph.
    """
    success = graph_store.remove_entity(id)
    if not success:
        raise HTTPException(status_code=404, detail="Entity not found or could not be deleted")
    return {"status": "success", "message": f"Entity {id} deleted"}


@router.get("/relationships")
async def list_relationships(
    type: str | None = Query(None, description="Filter by relationship type (WORKS_ON, USES, etc.)"),
    source: str | None = Query(None, description="Filter by source entity name"),
    target: str | None = Query(None, description="Filter by target entity name"),
    min_confidence: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    limit: int = Query(100, ge=1, le=500, description="Maximum relationships to return"),
    offset: int = Query(0, ge=0, description="Offset pagination"),
):
    """
    List all knowledge graph relationships with confidence and direction.
    """
    rels = graph_store.list_relationships(
        relation_type=type, source=source, target=target, min_confidence=min_confidence, limit=limit, offset=offset
    )
    return {"data": rels, "count": len(rels)}


@router.post("/relationships")
async def create_relationship(req: RelationshipCreateRequest):
    """
    Manually create or reinforce a relationship in the knowledge graph.
    """
    try:
        saved = graph_store.add_relationship(
            source_name=req.source,
            target_name=req.target,
            relation_type=req.type,
            confidence=req.confidence,
            context=req.context,
            metadata=req.metadata,
        )
        return {"status": "success", "relationship": saved}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/subgraph")
async def get_subgraph(
    entity: str | None = Query(None, description="Center entity name to extract ego-graph"),
    depth: int = Query(1, ge=1, le=3, description="Graph traversal hop depth"),
    max_nodes: int = Query(30, ge=1, le=200, description="Maximum nodes in returned subgraph"),
):
    """
    Retrieve subgraph for D3.js force-directed graph visualization.
    Returns nodes and links/edges formatted with coordinates readiness.
    """
    subgraph = graph_store.get_subgraph(entity_name=entity, depth=depth, max_nodes=max_nodes)
    return subgraph


@router.get("/path")
async def find_path(
    source: str = Query(..., description="Source entity name"),
    target: str = Query(..., description="Target entity name"),
):
    """
    Computes shortest path between two entities in the knowledge graph.
    """
    path = graph_store.find_path(source, target)
    if path is None:
        raise HTTPException(status_code=404, detail=f"No path found between '{source}' and '{target}'")
    return {"source": source, "target": target, "path": path}


@router.post("/extract")
async def extract_from_text(req: ExtractKnowledgeRequest):
    """
    Manually triggers ATLAS entity and relationship extraction on text using the local LLM.
    """
    result = await entity_extractor.extract_and_store(req.text, session_id=req.session_id)
    return {"status": "success", "extracted": result}


@router.get("/stats")
async def get_graph_stats():
    """
    Returns global graph metrics: total entities, relationships, and type breakdowns.
    """
    stats = graph_store.get_stats()
    return {"status": "success", "stats": stats}
