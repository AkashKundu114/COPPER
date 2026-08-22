import pytest
from app.ai.memory.vector_store import VectorStore


def test_vector_store_initialization():
    vs = VectorStore("test_mem_collection")
    assert vs.collection_name == "test_mem_collection"


@pytest.mark.asyncio
async def test_vector_store_add_document():
    vs = VectorStore("test_mem_collection")
    doc_id = await vs.add("FastAPI is an async web framework for Python", metadata={"tag": "python"})
    assert isinstance(doc_id, str)
    assert len(doc_id) > 0


@pytest.mark.asyncio
async def test_vector_store_search():
    vs = VectorStore("test_mem_collection")
    results = await vs.search("Python frameworks", n_results=3)
    assert isinstance(results, list)


@pytest.mark.asyncio
async def test_vector_store_count():
    vs = VectorStore("test_mem_collection")
    cnt = await vs.count()
    assert isinstance(cnt, int)
    assert cnt >= 0


@pytest.mark.asyncio
async def test_vector_store_search_with_where():
    vs = VectorStore("test_mem_collection")
    results = await vs.search("web framework", where={"tag": "python"})
    assert isinstance(results, list)
