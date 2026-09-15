"""
Unit tests for Crash-Consistent Write-Ahead Log (WAL) & Idempotent Agent Checkpointing.
Verifies CRC32 checksums, crash recovery analysis, idempotency keys, and compensation rollbacks.
"""

import tempfile
from pathlib import Path
import pytest

from app.ai.orchestration.wal_executor import (
    CrashRecoveryEngine,
    RecordType,
    TaskWAL,
    WALRecord,
)


def test_wal_record_crc32_checksum():
    payload = {"task_id": "T1", "instruction": "Write file", "agent": "AXIS"}
    rec = WALRecord(
        seq_num=1,
        timestamp=1700000000.0,
        dag_id="test_dag_1",
        record_type=RecordType.TASK_INTENT,
        payload=payload,
    )
    json_line = rec.to_json_line()
    assert rec.checksum != 0

    # Parse back
    parsed = WALRecord.from_json_line(json_line)
    assert parsed.seq_num == 1
    assert parsed.dag_id == "test_dag_1"
    assert parsed.record_type == RecordType.TASK_INTENT
    assert parsed.checksum == rec.checksum


def test_wal_corrupt_entry_detection():
    payload = {"task_id": "T1", "instruction": "Clean database"}
    rec = WALRecord(
        seq_num=1,
        timestamp=1700000000.0,
        dag_id="test_dag_corrupt",
        record_type=RecordType.TASK_INTENT,
        payload=payload,
    )
    json_line = rec.to_json_line()

    # Tamper with the line (change payload without updating checksum)
    tampered = json_line.replace("Clean database", "DROP TABLE users")
    with pytest.raises(ValueError, match="checksum mismatch"):
        WALRecord.from_json_line(tampered)


def test_wal_append_and_read_records():
    with tempfile.TemporaryDirectory() as tmp_dir:
        wal_dir = Path(tmp_dir)
        wal = TaskWAL(dag_id="dag_abc", wal_dir=wal_dir)

        wal.append_record(RecordType.DAG_START, {"goal": "build dashboard"})
        wal.append_record(RecordType.TASK_INTENT, {"task_id": "T1", "agent": "KINESIS"})
        wal.append_record(RecordType.TASK_COMMIT, {"task_id": "T1", "output": "Dashboard spec generated"})
        wal.append_record(RecordType.DAG_COMMIT, {"status": "success"})

        records = wal.read_records()
        assert len(records) == 4
        assert records[0].record_type == RecordType.DAG_START
        assert records[2].record_type == RecordType.TASK_COMMIT
        assert records[3].record_type == RecordType.DAG_COMMIT


def test_crash_recovery_engine_detects_incomplete_dag():
    with tempfile.TemporaryDirectory() as tmp_dir:
        wal_dir = Path(tmp_dir)
        engine = CrashRecoveryEngine(wal_dir=wal_dir)

        # 1. Complete DAG
        wal1 = TaskWAL(dag_id="complete_1", wal_dir=wal_dir)
        wal1.append_record(RecordType.DAG_START, {"goal": "complete"})
        wal1.append_record(RecordType.DAG_COMMIT, {"status": "done"})

        # 2. Incomplete (interrupted mid-flight) DAG
        wal2 = TaskWAL(dag_id="crashed_2", wal_dir=wal_dir)
        wal2.append_record(RecordType.DAG_START, {"goal": "crashed midway"})
        wal2.append_record(RecordType.TASK_INTENT, {"task_id": "T1", "agent": "AXIS"})
        wal2.append_record(RecordType.TASK_COMMIT, {"task_id": "T1", "output": "T1 done"})
        wal2.append_record(RecordType.TASK_INTENT, {"task_id": "T2", "agent": "FORGE"})
        # No DAG_COMMIT!

        incomplete = engine.find_incomplete_dags()
        assert "crashed_2" in incomplete
        assert "complete_1" not in incomplete


def test_crash_recovery_engine_state_analysis_and_rollback():
    with tempfile.TemporaryDirectory() as tmp_dir:
        wal_dir = Path(tmp_dir)
        engine = CrashRecoveryEngine(wal_dir=wal_dir)

        wal = TaskWAL(dag_id="crash_with_mutation", wal_dir=wal_dir)
        wal.append_record(RecordType.DAG_START, {"goal": "generate code"})

        # Task 1 committed
        wal.append_record(RecordType.TASK_COMMIT, {"task_id": "T1", "output": "T1 output"})

        # Task 2 created an orphaned file but process died before committing!
        orphaned_file = Path(tmp_dir) / "orphaned_script.py"
        orphaned_file.write_text("print('half-written')", encoding="utf-8")
        assert orphaned_file.exists()

        wal.append_record(
            RecordType.MUTATION_RECORD,
            {"task_id": "T2", "type": "file_created", "path": str(orphaned_file)},
        )
        # Process crash here! (no TASK_COMMIT for T2)

        state = engine.analyze_dag_state("crash_with_mutation")
        assert state["is_complete"] is False
        assert "T1" in state["committed_tasks"]
        assert len(state["uncommitted_mutations"]) == 1

        # Execute compensation rollback
        rollbacks = engine.rollback_uncommitted_mutations("crash_with_mutation")
        assert rollbacks == 1
        assert not orphaned_file.exists()  # Orphaned file deleted!

        records_after = wal.read_records()
        last_rec = records_after[-1]
        assert last_rec.record_type == RecordType.DAG_ABORT
