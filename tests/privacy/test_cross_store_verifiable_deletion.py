import hashlib
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.privacy.governance_manager import (
    DataGovernanceManager,
    DeletionReceipt,
)
from app.database.models.history import ChatHistory
from app.database.models.memory_v2 import UserMemoryV2


def test_deletion_receipt_verification_hash():
    """Verify DeletionReceipt calculates tamper-evident SHA-256 verification hash."""
    gov = DataGovernanceManager()
    receipt_id = "test-receipt-123"
    timestamp = "2026-11-10T12:00:00Z"
    counts = {"relational_memories": 5, "chromadb_vectors": 5, "file_artifacts": 2}

    h1 = gov.compute_verification_hash(receipt_id, timestamp, counts)
    assert len(h1) == 64  # SHA-256 hex string

    # Modifying counts must produce completely different hash
    counts_tampered = {"relational_memories": 4, "chromadb_vectors": 5, "file_artifacts": 2}
    h2 = gov.compute_verification_hash(receipt_id, timestamp, counts_tampered)
    assert h1 != h2


@pytest.mark.asyncio
async def test_execute_verifiable_full_deletion_mock():
    """Verify execute_verifiable_full_deletion purges across relational, vector, cache, and files."""
    gov = DataGovernanceManager()
    mock_db = MagicMock()
    mock_db.query.return_value.delete.return_value = 10

    with patch("app.ai.memory.vector_store.VectorStore.clear", new_callable=AsyncMock) as mock_chroma_clear, \
         patch("app.ai.memory.vector_store.VectorStore.count", new_callable=AsyncMock) as mock_chroma_count:
        mock_chroma_count.return_value = 4
        mock_chroma_clear.return_value = True

        receipt = await gov.execute_verifiable_full_deletion(mock_db, operator="test_admin")

        assert receipt.verified is True
        assert receipt.target_scope == "full_system_wipe"
        assert receipt.records_deleted["relational_memories"] == 10
        assert receipt.records_deleted["chromadb_vectors"] >= 4
        assert len(receipt.verification_hash) == 64
        assert mock_db.commit.called


@pytest.mark.asyncio
async def test_delete_single_memory_cascades_to_vector_store():
    """Verify deleting single memory cascades to both relational DB and ChromaDB vector store."""
    gov = DataGovernanceManager()
    mock_db = MagicMock()
    fake_mem = UserMemoryV2(id=42, content="Secret user note")
    mock_db.query.return_value.filter.return_value.first.return_value = fake_mem

    with patch("app.ai.memory.vector_store.VectorStore.delete", new_callable=AsyncMock) as mock_vs_del:
        mock_vs_del.return_value = 1

        receipt = await gov.delete_single_memory(mock_db, memory_id=42)

        assert receipt.records_deleted["relational_memories"] == 1
        assert receipt.records_deleted["chromadb_vectors"] == 1
        assert mock_db.delete.called
        assert mock_db.commit.called
        mock_vs_del.assert_called_once_with(["42"])
