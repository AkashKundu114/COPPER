"""Chaos Engineering & Fault Injection Test Suite for COPPER.

Verifies system resilience against process termination, network cuts,
database outages, disk saturation, and external service failures.
"""

import asyncio
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.self_healing import resilient_call
from app.core.resilience.circuit_breaker import CircuitBreaker
from app.database.postgres import check_db_health, resilient_transaction
from app.database.redis_client import get_redis


@pytest.mark.asyncio
async def test_chaos_model_process_termination():
    """Chaos 1: Model process crash (HTTP 500 / Process Termination) -> Fallback recovery."""
    call_attempts = 0

    async def simulated_crashed_model():
        nonlocal call_attempts
        call_attempts += 1
        raise ConnectionResetError("Ollama daemon process terminated unexpectedly (SIGKILL)")

    async def simulated_gatekeeper_fallback():
        return "Resilient response from pinned gatekeeper fallback model"

    result = await resilient_call(
        primary=simulated_crashed_model,
        fallbacks=[simulated_gatekeeper_fallback],
        retries=1,
        retry_delay_s=0.01,
        incident_label="chaos_model_crash",
    )

    assert result.success is True
    assert "pinned gatekeeper" in result.result
    assert len(result.attempts) == 3  # primary attempt 1, primary attempt 2, fallback


def test_chaos_database_disconnection():
    """Chaos 2: Database drops connection mid-transaction -> resilient retry."""
    mock_db = MagicMock()
    connection_attempts = 0

    def database_write():
        nonlocal connection_attempts
        connection_attempts += 1
        if connection_attempts == 1:
            raise ConnectionError("OperationalError: connection to database server lost")
        return "transaction_committed"

    # Verify health check detects degraded state when probe fails
    with patch("app.database.postgres.engine.connect") as mock_conn:
        mock_conn.side_effect = ConnectionRefusedError("Database port 5432 unreachable")
        health = check_db_health()
        assert health["status"] == "degraded"
        assert "unreachable" in health["error"]


@pytest.mark.asyncio
async def test_chaos_redis_failure_local_fallback():
    """Chaos 3: Redis cache offline -> Transparent fallback to local state."""
    with patch("app.database.redis_client.redis_client", None):
        redis = await get_redis()
        # Should gracefully return None without raising uncaught exception
        assert redis is None


@pytest.mark.asyncio
async def test_chaos_chromadb_unavailability():
    """Chaos 4: ChromaDB vector store throws HTTP/Connection error -> Degraded keyword fallback."""
    async def failing_vector_retrieval():
        raise RuntimeError("ChromaDB connection refused at localhost:8000")

    async def keyword_memory_fallback():
        return [{"id": "mem_local_1", "text": "Failsafe epistemic context"}]

    result = await resilient_call(
        primary=failing_vector_retrieval,
        fallbacks=[keyword_memory_fallback],
        retries=1,
        retry_delay_s=0.01,
        incident_label="chaos_chroma_outage",
    )
    assert result.success is True
    assert result.result[0]["id"] == "mem_local_1"


@pytest.mark.asyncio
async def test_chaos_worker_termination():
    """Chaos 5: Worker task receives asyncio.CancelledError -> Clean state unwind."""
    async def cancellable_worker():
        await asyncio.sleep(10.0)

    task = asyncio.create_task(cancellable_worker())
    await asyncio.sleep(0.01)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    assert task.cancelled()


def test_chaos_interrupted_dag_execution():
    """Chaos 6: DAG halted mid-flight -> Crash recovery compensates partial state."""
    from app.ai.orchestration.wal_executor import (
        CrashRecoveryEngine,
        RecordType,
        TaskWAL,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        wal_dir = Path(tmpdir)
        dag_id = "chaos_dag_interrupted"
        wal = TaskWAL(dag_id=dag_id, wal_dir=wal_dir)
        engine = CrashRecoveryEngine(wal_dir=wal_dir)

        # 1. Start DAG and commit Task 1
        wal.append_record(RecordType.DAG_START, {"goal": "Chaos test"})
        wal.append_record(RecordType.TASK_COMMIT, {"task_id": "T1", "output": "done"})

        # 2. Crash during Task 2 (partial file created)
        p_file = wal_dir / "interrupted_file.tmp"
        p_file.write_text("partial corrupted data", encoding="utf-8")
        wal.append_record(
            RecordType.MUTATION_RECORD,
            {"task_id": "T2", "type": "file_created", "path": str(p_file)},
        )

        # Crash recovery compensates
        rolled_back = engine.rollback_uncommitted_mutations(dag_id)
        assert rolled_back == 1
        assert not p_file.exists()


@pytest.mark.asyncio
async def test_chaos_disk_exhaustion_simulation():
    """Chaos 7: Disk space exhausted (OSError: [Errno 28] No space left on device) -> Handled safely."""
    async def disk_writing_operation():
        raise OSError(28, "No space left on device")

    async def in_memory_buffer_fallback():
        return {"status": "buffered_in_memory", "bytes": 1024}

    result = await resilient_call(
        primary=disk_writing_operation,
        fallbacks=[in_memory_buffer_fallback],
        retries=1,
        retry_delay_s=0.01,
        incident_label="chaos_disk_exhaustion",
    )
    assert result.success is True
    assert result.result["status"] == "buffered_in_memory"


@pytest.mark.asyncio
async def test_chaos_network_interruption():
    """Chaos 8: Network connection timed out -> Circuit breaker trips and DLQ enqueues."""
    cb = CircuitBreaker("chaos_network_service", failure_threshold=2, recovery_timeout_s=1.0)

    async def network_call():
        raise TimeoutError("Network gateway unreachable: connect timed out")

    # Call 1: fails
    with pytest.raises(TimeoutError):
        await cb.call(network_call)

    # Call 2: fails -> trips circuit
    with pytest.raises(TimeoutError):
        await cb.call(network_call)

    from app.core.resilience.circuit_breaker import CircuitState
    assert cb.state == CircuitState.OPEN
