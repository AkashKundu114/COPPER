"""
Unit tests for Symbol-Preserving Hybrid RRF Retriever.
Verifies tokenization preservation, query intent classification, and RRF ranking logic.
"""

import pytest

from app.ai.memory.hybrid_retriever import (
    HybridRRFRetriever,
    QueryIntent,
    SymbolPreservingTokenizer,
)


def test_symbol_preserving_tokenizer():
    query = "Where is get_user_by_id defined in auth_service.py with error 0x80070005?"
    tokens = SymbolPreservingTokenizer.tokenize(query)

    # Must preserve exact compound identifiers
    assert "get_user_by_id" in tokens
    assert "auth_service.py" in tokens
    assert "0x80070005" in tokens


def test_classify_intent_code_symbol():
    retriever = HybridRRFRetriever()
    intent, w_dense, w_lex = retriever.classify_intent("find function parse_task_graph_json")
    assert intent == QueryIntent.CODE_SYMBOL
    assert w_lex > w_dense  # Lexical boosted for code symbols


def test_classify_intent_semantic_question():
    retriever = HybridRRFRetriever()
    intent, w_dense, w_lex = retriever.classify_intent(
        "What was our architectural philosophy regarding local privacy and zero cloud egress?"
    )
    assert intent == QueryIntent.SEMANTIC
    assert w_dense > w_lex  # Semantic boosted for natural language questions


def test_classify_intent_balanced():
    retriever = HybridRRFRetriever()
    intent, w_dense, w_lex = retriever.classify_intent("database setup")
    assert intent == QueryIntent.BALANCED
    assert w_dense == 0.50
    assert w_lex == 0.50


@pytest.mark.asyncio
async def test_hybrid_retriever_ranking_both_sources_beats_single():
    # Mock doc_store and bm25
    class MockDocStore:
        async def search(self, query, n_results=10):
            return [
                {"document": "Doc A: general context", "distance": 0.2, "metadata": {"id": "1"}},
                {"document": "Doc B: exact match", "distance": 0.3, "metadata": {"id": "2"}},
            ]

    retriever = HybridRRFRetriever(doc_store=MockDocStore())

    # Mock bm25 results where Doc B is rank 1 and Doc C is rank 2
    import app.ai.memory.hybrid_retriever as hr
    original_bm25 = hr.bm25_index

    class MockBM25:
        def search_documents(self, query, limit=10):
            return [
                {"content": "Doc B: exact match", "bm25_score": 12.5, "metadata": {"id": "2"}},
                {"content": "Doc C: keyword only", "bm25_score": 8.0, "metadata": {"id": "3"}},
            ]

    hr.bm25_index = MockBM25()
    try:
        results = await retriever.search("test query", limit=5)
        # Doc B appeared in BOTH dense and lexical lists -> its RRF score must be highest!
        assert results[0]["content"] == "Doc B: exact match"
        assert results[0]["dense_rank"] is not None
        assert results[0]["lexical_rank"] is not None
    finally:
        hr.bm25_index = original_bm25
