import pytest
from fastapi.testclient import TestClient

from app.ai.knowledge.entity_extractor import entity_extractor
from app.ai.knowledge.graph_rag import graph_rag
from app.ai.knowledge.graph_store import bayesian_confidence_update, canonicalize_name, graph_store
from app.database.models.knowledge_graph import KnowledgeEntity, KnowledgeRelationship
from app.database.postgres import SessionLocal, init_db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_knowledge_db():
    init_db()
    db = SessionLocal()
    try:
        db.query(KnowledgeRelationship).delete()
        db.query(KnowledgeEntity).delete()
        db.commit()
    finally:
        db.close()
    graph_store.initialize_sync()


def test_canonicalize_name():
    assert canonicalize_name("  COPPER  ") == "copper"
    assert canonicalize_name("FastAPI   Framework") == "fastapi framework"
    assert canonicalize_name("") == ""


def test_bayesian_confidence_update():
    # Independent confirmation should increase confidence monotonically
    prior = 0.8
    updated = bayesian_confidence_update(prior, 0.9)
    assert updated > prior
    assert updated <= 0.99

    # Reinforce again
    updated2 = bayesian_confidence_update(updated, 0.95)
    assert updated2 > updated
    assert updated2 <= 0.99


def test_add_entity_and_deduplication():
    # Add new entity
    ent1 = graph_store.add_entity(
        name="COPPER",
        entity_type="PROJECT",
        confidence=0.85,
        context="Personal AI Operating System",
    )
    assert ent1["name"] == "COPPER"
    assert ent1["canonical_name"] == "copper"
    assert ent1["type"] == "PROJECT"
    assert ent1["evidence_count"] == 1
    assert ent1["confidence"] == 0.85

    # Re-add with slightly different casing (deduplication test)
    ent2 = graph_store.add_entity(
        name="copper",
        entity_type="PROJECT",
        confidence=0.90,
        context="Personal AI OS with local models",
    )
    assert ent2["id"] == ent1["id"]
    assert ent2["evidence_count"] == 2
    assert ent2["confidence"] > 0.85  # Bayesian increase


def test_add_relationship_and_deduplication():
    # Add relationship
    rel1 = graph_store.add_relationship(
        source_name="Akash",
        target_name="COPPER",
        relation_type="WORKS_ON",
        confidence=0.95,
        context="Primary architect",
    )
    assert rel1["source"] == "Akash"
    assert rel1["target"] == "COPPER"
    assert rel1["type"] == "WORKS_ON"
    assert rel1["evidence_count"] == 1
    assert rel1["confidence"] == 0.95

    # Confirm same relationship again
    rel2 = graph_store.add_relationship(
        source_name="akash",
        target_name="copper",
        relation_type="WORKS_ON",
        confidence=0.95,
    )
    assert rel2["id"] == rel1["id"]
    assert rel2["evidence_count"] == 2
    assert rel2["confidence"] >= 0.95


def test_query_neighbors_and_subgraph():
    graph_store.add_relationship(
        source_name="COPPER",
        target_name="FastAPI",
        relation_type="USES",
        confidence=0.90,
    )
    graph_store.add_relationship(
        source_name="FastAPI",
        target_name="Python",
        relation_type="DEPENDS_ON",
        confidence=0.92,
    )

    # 1-hop neighbors of COPPER
    neighbors = graph_store.query_neighbors("COPPER", depth=1)
    node_canons = [n["canonical_name"] for n in neighbors["nodes"]]
    assert "copper" in node_canons
    assert "fastapi" in node_canons

    # Subgraph for D3
    subgraph = graph_store.get_subgraph("COPPER", depth=1)
    assert "nodes" in subgraph
    assert "links" in subgraph
    assert len(subgraph["nodes"]) >= 2
    assert any(e["type"] == "USES" for e in subgraph["links"])


def test_find_path():
    graph_store.add_relationship("Akash", "COPPER", "WORKS_ON", 0.95)
    graph_store.add_relationship("COPPER", "FastAPI", "USES", 0.90)
    graph_store.add_relationship("FastAPI", "Starlette", "DEPENDS_ON", 0.88)

    path = graph_store.find_path("Akash", "Starlette")
    assert path is not None
    assert len(path) == 4  # Akash -> COPPER -> FastAPI -> Starlette
    assert path[0]["entity"]["canonical_name"] == "akash"
    assert path[-1]["entity"]["canonical_name"] == "starlette"

    # Disconnected node
    graph_store.add_entity("Moon", "LOCATION", 0.7)
    no_path = graph_store.find_path("Akash", "Moon")
    assert no_path is None


def test_remove_entity():
    temp_ent = graph_store.add_entity("TempDeleteEntity", "CONCEPT", 0.8)
    graph_store.add_relationship("TempDeleteEntity", "COPPER", "RELATED_TO", 0.8)

    ent_id = temp_ent["id"]
    assert graph_store.query_entity(ent_id) is not None

    deleted = graph_store.remove_entity(ent_id)
    assert deleted is True
    assert graph_store.query_entity(ent_id) is None
    assert graph_store.query_entity("TempDeleteEntity") is None


def test_entity_extractor_parser_xml_format():
    sample_output = """
    Here are the extracted entities and relationships:
    <entities>
    [{"name": "COPPER", "type": "PROJECT", "confidence": 0.95, "context": "personal AI OS"},
     {"name": "FastAPI", "type": "TECHNOLOGY", "confidence": 0.90, "context": "web framework"}]
    </entities>
    <relationships>
    [{"source": "COPPER", "target": "FastAPI", "type": "USES", "confidence": 0.90}]
    </relationships>
    """
    entities, relationships = entity_extractor.parse_extraction_output(sample_output)
    assert len(entities) == 2
    assert entities[0]["name"] == "COPPER"
    assert entities[0]["type"] == "PROJECT"
    assert entities[0]["confidence"] == 0.95
    assert len(relationships) == 1
    assert relationships[0]["source"] == "COPPER"
    assert relationships[0]["target"] == "FastAPI"
    assert relationships[0]["type"] == "USES"


def test_entity_extractor_no_entities():
    sample_output = "NO_ENTITIES"
    entities, relationships = entity_extractor.parse_extraction_output(sample_output)
    assert entities == []
    assert relationships == []


def test_entity_extractor_markdown_json():
    sample_output = """
    <entities>
    ```json
    [
      {"name": "Akash", "type": "PERSON", "confidence": 0.98}
    ]
    ```
    </entities>
    <relationships>
    ```json
    [
      {"source": "Akash", "target": "COPPER", "type": "WORKS_ON", "confidence": 0.98}
    ]
    ```
    </relationships>
    """
    entities, relationships = entity_extractor.parse_extraction_output(sample_output)
    assert len(entities) == 1
    assert entities[0]["name"] == "Akash"
    assert entities[0]["type"] == "PERSON"
    assert len(relationships) == 1
    assert relationships[0]["source"] == "Akash"
    assert relationships[0]["type"] == "WORKS_ON"


def test_graph_rag_context_formatting():
    rels = [
        {"source": "Akash", "target": "COPPER", "type": "WORKS_ON", "confidence": 0.95},
        {"source": "COPPER", "target": "FastAPI", "type": "USES", "confidence": 0.90},
    ]
    context = graph_rag.format_graph_context(rels)
    expected_lines = [
        "KNOWLEDGE GRAPH CONTEXT:",
        "- Akash WORKS_ON COPPER (confidence: 95%)",
        "- COPPER USES FastAPI (confidence: 90%)",
    ]
    assert context == "\n".join(expected_lines)


@pytest.mark.asyncio
async def test_graph_rag_get_graph_context():
    graph_store.add_relationship("Akash", "COPPER", "WORKS_ON", 0.95)
    graph_store.add_relationship("COPPER", "FastAPI", "USES", 0.90)

    # Query mentioning COPPER
    ctx = await graph_rag.get_graph_context("What technologies does COPPER use and who works on it?")
    assert "KNOWLEDGE GRAPH CONTEXT:" in ctx
    assert "Akash WORKS_ON COPPER" in ctx
    assert "COPPER USES FastAPI" in ctx


def test_api_routes_knowledge_graph():
    # 1. Create entity via POST
    res_ent = client.post(
        "/api/v1/knowledge/entities",
        json={"name": "ChromaDB", "type": "TECHNOLOGY", "confidence": 0.92, "context": "vector database"},
    )
    assert res_ent.status_code == 200
    ent_data = res_ent.json()["entity"]
    ent_id = ent_data["id"]

    # 2. Get entity
    res_get = client.get(f"/api/v1/knowledge/entities/{ent_id}")
    assert res_get.status_code == 200
    assert res_get.json()["entity"]["name"] == "ChromaDB"

    # 3. Create relationship via POST
    res_rel = client.post(
        "/api/v1/knowledge/relationships",
        json={"source": "COPPER", "target": "ChromaDB", "type": "USES", "confidence": 0.93},
    )
    assert res_rel.status_code == 200
    assert res_rel.json()["relationship"]["type"] == "USES"

    # 4. List entities
    res_list_ent = client.get("/api/v1/knowledge/entities?search=ChromaDB")
    assert res_list_ent.status_code == 200
    assert len(res_list_ent.json()["data"]) >= 1

    # 5. List relationships
    res_list_rel = client.get("/api/v1/knowledge/relationships?type=USES")
    assert res_list_rel.status_code == 200
    assert len(res_list_rel.json()["data"]) >= 1

    # 6. Subgraph endpoint
    res_sub = client.get("/api/v1/knowledge/subgraph?entity=COPPER")
    assert res_sub.status_code == 200
    sub_data = res_sub.json()
    assert "nodes" in sub_data
    assert "links" in sub_data

    # 7. Stats endpoint
    res_stats = client.get("/api/v1/knowledge/stats")
    assert res_stats.status_code == 200
    assert res_stats.json()["stats"]["total_entities"] >= 2

    # 8. Delete entity
    res_del = client.delete(f"/api/v1/knowledge/entities/{ent_id}")
    assert res_del.status_code == 200
    assert res_del.json()["status"] == "success"
