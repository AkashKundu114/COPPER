import tempfile
from pathlib import Path
from unittest.mock import MagicMock
import pytest

from app.database.postgres import (
    check_db_health,
    checkpoint_wal,
    verify_and_backup_db,
    resilient_transaction,
    execute_resilient_transaction,
)


def test_check_db_health():
    """Verify check_db_health reports healthy connection."""
    health = check_db_health()
    assert health["status"] == "healthy"
    assert health["latency_ms"] >= 0.0


def test_sqlite_wal_checkpoint_and_backup():
    """Verify SQLite WAL checkpointing and verified backup creation."""
    chk = checkpoint_wal("PASSIVE")
    assert chk["status"] in ("success", "skipped")

    with tempfile.TemporaryDirectory() as tmpdir:
        backup_res = verify_and_backup_db(backup_dir=Path(tmpdir))
        assert backup_res["status"] in ("success", "skipped")
        if backup_res["status"] == "success":
            assert backup_res["integrity"] == "ok"
            assert Path(backup_res["backup_path"]).exists()


def test_resilient_transaction_context_manager_rolls_back():
    """Verify resilient_transaction rolls back when an exception is raised."""
    mock_db = MagicMock()
    with pytest.raises(ValueError):
        with resilient_transaction(mock_db):
            raise ValueError("Test transaction failure")
    assert mock_db.rollback.called


def test_execute_resilient_transaction_retries_transient_lock():
    """Verify execute_resilient_transaction catches transient SQLite locks and succeeds on retry."""
    mock_db = MagicMock()
    call_counts = 0

    def flaky_operation(session):
        nonlocal call_counts
        call_counts += 1
        if call_counts == 1:
            raise RuntimeError("OperationalError: database is locked")
        return "success"

    res = execute_resilient_transaction(mock_db, flaky_operation, max_retries=2, base_delay_s=0.01)
    assert res == "success"
    assert call_counts == 2
    assert mock_db.commit.called
