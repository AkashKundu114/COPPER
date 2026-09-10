import pytest
from unittest.mock import AsyncMock, patch

from app.ai.agents.research_agent import CITATION_GROUNDED_RESEARCH_PROMPT_TEMPLATE, research_agent
from app.ai.memory.bm25_index import BM25Index, tokenize_text
from app.ai.memory.hybrid_search import HybridSearch
from app.ai.memory.reranker import LocalReRanker


# ---------------------------------------------------------
# BM25 Index Tests
# ---------------------------------------------------------

def test_tokenize_text():
    tokens = tokenize_text("Quantum Computing & Neural-Networks (v1.5)!")
    assert "quantum" in tokens
    assert "computing" in tokens
    assert "neural" in tokens
    assert "networks" in tokens
    assert "v1" in tokens
    assert "5" in tokens


def test_bm25_add_search_remove():
    index = BM25Index(auto_bootstrap=False)
    index.clear()

    index.add_document("doc_1", "Deep learning algorithms utilize gradient descent optimization.")
    index.add_document("doc_2", "Quantum cryptography ensures information-theoretic security via qubits.")
    index.add_document("doc_3", "Automated deployment pipelines streamline container orchestration.")

    assert index.count() == 3

    # Keyword search for quantum
    results = index.search("quantum qubits", limit=5)
    assert len(results) >= 1
    top_doc_id, top_score = results[0]
    assert top_doc_id == "doc_2"
    assert top_score > 0.0

    # Search with full documents
    doc_results = index.search_documents("deployment pipelines", limit=2)
    assert len(doc_results) >= 1
    assert doc_results[0]["doc_id"] == "doc_3"
    assert "Automated deployment" in doc_results[0]["content"]

    # Remove document
    assert index.remove_document("doc_2") is True
    assert index.count() == 2
    res_after = index.search("quantum qubits", limit=5)
    assert not any(d_id == "doc_2" for d_id, _ in res_after)


def test_bm25_auto_update_batch():
    index = BM25Index(auto_bootstrap=False)
    index.clear()

    items = [
        {"id": "b1", "content": "Database sharding distributes records across partitions."},
        {"id": "b2", "content": "Cache invalidation uses TTL and write-through policies."},
    ]
    index.add_documents(items)
    assert index.count() == 2

    # Query matching newly added item
    results = index.search("sharding partitions", limit=2)
    assert len(results) >= 1
    assert results[0][0] == "b1"


# ---------------------------------------------------------
# Hybrid Search with Reciprocal Rank Fusion (RRF) Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_hybrid_search_rrf_scoring():
    mock_vector_store = AsyncMock()
    # Vector store returns docA at rank 1, docB at rank 2
    mock_vector_store.search.return_value = [
        {"document": "Artificial intelligence architectures", "metadata": {"id": "docA"}, "distance": 0.20},
        {"document": "Cloud computing virtualization", "metadata": {"id": "docB"}, "distance": 0.80},
    ]

    hybrid = HybridSearch(doc_store=mock_vector_store, rrf_k=60)

    # Populate BM25 index with docA (at rank 1) and docC (at rank 2)
    with patch("app.ai.memory.hybrid_search.bm25_index") as mock_bm25:
        mock_bm25.search_documents.return_value = [
            {"doc_id": "docA", "content": "Artificial intelligence architectures", "metadata": {"id": "docA"}, "bm25_score": 12.5, "source": "document"},
            {"doc_id": "docC", "content": "Relational database indexing", "metadata": {"id": "docC"}, "bm25_score": 8.2, "source": "document"},
        ]

        results = await hybrid.search("artificial intelligence", limit=5, rrf_k=60)

        assert len(results) == 3

        # docA appears in BOTH vector (rank 1) and BM25 (rank 1)
        # Expected RRF score = 1/(60+1) + 1/(60+1) = 2/61 ≈ 0.032787
        docA = next(r for r in results if r["doc_id"] == "docA")
        assert docA["vector_rank"] == 1
        assert docA["bm25_rank"] == 1
        expected_docA_rrf = round((1.0 / 61.0) + (1.0 / 61.0), 6)
        assert abs(docA["rrf_score"] - expected_docA_rrf) < 1e-4

        # docB only in vector (rank 2) -> 1/(60+2) = 1/62 ≈ 0.016129
        docB = next(r for r in results if r["doc_id"] == "docB")
        assert docB["vector_rank"] == 2
        assert docB["bm25_rank"] is None
        expected_docB_rrf = round(1.0 / 62.0, 6)
        assert abs(docB["rrf_score"] - expected_docB_rrf) < 1e-4

        # docC only in BM25 (rank 2) -> 1/(60+2) = 1/62 ≈ 0.016129
        docC = next(r for r in results if r["doc_id"] == "docC")
        assert docC["vector_rank"] is None
        assert docC["bm25_rank"] == 2

        # Top result must be docA due to dual presence
        assert results[0]["doc_id"] == "docA"


# ---------------------------------------------------------
# Re-Ranker Tests
# ---------------------------------------------------------

@pytest.mark.asyncio
async def test_reranker_heuristic_scoring():
    reranker_inst = LocalReRanker()

    candidates = [
        {
            "content": "Deep reinforcement learning utilizes policy gradients and value functions.",
            "vector_similarity": 0.85,
            "rrf_score": 0.030,
        },
        {
            "content": "Baking sourdough bread requires flour, water, salt, and wild yeast culture.",
            "vector_similarity": 0.20,
            "rrf_score": 0.015,
        },
        {
            "content": "Reinforcement learning agents maximize cumulative reward in Markov decision processes.",
            "vector_similarity": 0.80,
            "rrf_score": 0.025,
        },
    ]

    # Re-rank with query regarding reinforcement learning
    reranked = await reranker_inst.rerank("reinforcement learning gradients", candidates, top_n=2)

    assert len(reranked) == 2
    for r in reranked:
        assert "relevance_score" in r
        assert 0.0 <= r["relevance_score"] <= 1.0

    # Top result should be the policy gradients passage
    assert "policy gradients" in reranked[0]["content"]
    # Sourdough passage must score significantly lower or not be in top 2
    assert reranked[0]["relevance_score"] > 0.50


@pytest.mark.asyncio
async def test_reranker_with_mock_llm():
    reranker_inst = LocalReRanker()

    candidates = [
        {"content": "Passage Alpha", "vector_similarity": 0.5},
        {"content": "Passage Beta", "vector_similarity": 0.5},
    ]

    with patch("app.ai.llm.ollama_client.ollama_client.is_available", AsyncMock(return_value=True)):
        with patch("app.ai.llm.ollama_client.ollama_client.chat", AsyncMock(return_value='{"relevance": 0.92, "reasoning": "Direct match"}')):
            reranked = await reranker_inst.rerank("test query", candidates, top_n=2)
            assert len(reranked) == 2
            assert reranked[0]["relevance_score"] == 0.92
            assert reranked[0]["rerank_reasoning"] == "Direct match"


# ---------------------------------------------------------
# Research Agent Citation Grounding Tests
# ---------------------------------------------------------

def test_research_agent_format_ranked_sources():
    sources = [
        {
            "content": "Asyncio TaskGroup manages lifecycle of concurrent coroutines.",
            "relevance_score": 0.95,
            "source": "concurrency_docs.md",
            "metadata": {"filename": "concurrency_docs.md"},
        },
        {
            "content": "Pydantic V2 offers core validation written in Rust.",
            "relevance_score": 0.88,
            "source": "pydantic_guide.pdf",
            "metadata": {"filename": "pydantic_guide.pdf"},
        },
    ]

    formatted = research_agent.format_ranked_sources(sources)
    assert "[Source 1] (Relevance: 0.95, Source: concurrency_docs.md):" in formatted
    assert "Asyncio TaskGroup" in formatted
    assert "[Source 2] (Relevance: 0.88, Source: pydantic_guide.pdf):" in formatted
    assert "Pydantic V2" in formatted


@pytest.mark.asyncio
async def test_research_agent_citation_grounded_run():
    mock_sources = [
        {
            "content": "C.O.P.P.E.R. implements Hybrid RAG using Reciprocal Rank Fusion (k=60) and Qwen micro-reranking.",
            "relevance_score": 0.98,
            "metadata": {"filename": "system_specs.md"},
        }
    ]

    with patch.object(research_agent, "retrieve_and_rerank", AsyncMock(return_value=mock_sources)):
        with patch("app.ai.llm.ollama_client.ollama_client.chat", AsyncMock(return_value="COPPER uses Hybrid RAG with RRF k=60 [Source 1].")):
            response = await research_agent.run("How does COPPER implement RAG?")
            assert "[Source 1]" in response
            assert "Hybrid RAG" in response


@pytest.mark.asyncio
async def test_research_agent_programmatic_research_api():
    mock_sources = [
        {
            "content": "The system architecture uses 11 specialized agent personas.",
            "relevance_score": 0.94,
            "metadata": {"source": "specs.txt"},
        }
    ]

    with patch.object(research_agent, "retrieve_and_rerank", AsyncMock(return_value=mock_sources)):
        with patch.object(research_agent, "run", AsyncMock(return_value="COPPER features 11 agents [Source 1].")):
            result = await research_agent.research("How many agents does COPPER have?")
            assert result["query"] == "How many agents does COPPER have?"
            assert "[Source 1]" in result["answer"]
            assert len(result["sources"]) == 1
            assert result["sources"][0]["relevance_score"] == 0.94
