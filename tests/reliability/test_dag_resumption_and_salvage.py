import tempfile
from pathlib import Path
import pytest

from app.ai.orchestration.wal_executor import (
    CrashRecoveryEngine,
    RecordType,
    TaskWAL,
)


def test_can_resume_dag_and_prepare_resumption():
    """Verify interrupted DAG progress is preserved and uncommitted mutations are compensated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wal_dir = Path(tmpdir)
        dag_id = "test_resume_dag_1"
        wal = TaskWAL(dag_id=dag_id, wal_dir=wal_dir)
        recovery_engine = CrashRecoveryEngine(wal_dir=wal_dir)

        # 1. Start DAG
        wal.append_record(RecordType.DAG_START, {"goal": "Multi-agent research"})

        # 2. Task 1 completed
        wal.append_record(RecordType.TASK_INTENT, {"task_id": "T1", "agent": "OMNI"})
        wal.append_record(RecordType.TASK_COMMIT, {"task_id": "T1", "agent": "OMNI", "output": "Research findings"})

        # 3. Task 2 started in-flight mutation but crashed before commit
        orphan_file = wal_dir / "partial_orphan.txt"
        orphan_file.write_text("incomplete content", encoding="utf-8")
        wal.append_record(
            RecordType.MUTATION_RECORD,
            {"task_id": "T2", "type": "file_created", "path": str(orphan_file)},
        )

        # Assert resumable
        assert recovery_engine.can_resume_dag(dag_id) is True

        # Prepare resumption: orphan file must be compensated, T1 preserved
        prep = recovery_engine.prepare_dag_resumption(dag_id)
        assert prep["resumable"] is True
        assert "T1" in prep["committed_tasks"]
        assert prep["committed_tasks"]["T1"] == "Research findings"
        assert not orphan_file.exists()  # Orphaned uncommitted side effect compensated


def test_salvage_corrupted_wal_isolates_bad_lines():
    """Verify salvage_corrupted_wal isolates corrupted lines to quarantine without dropping valid records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        wal_dir = Path(tmpdir)
        dag_id = "corrupted_dag_99"
        wal = TaskWAL(dag_id=dag_id, wal_dir=wal_dir)
        recovery_engine = CrashRecoveryEngine(wal_dir=wal_dir)

        # Write valid record 1
        wal.append_record(RecordType.DAG_START, {"goal": "test"})

        # Inject corrupt raw JSON line
        with open(wal.file_path, "a", encoding="utf-8") as f:
            f.write('{"seq_num": 2, "timestamp": 12345, "dag_id": "corrupted_dag_99", "record_type": "TASK_INTENT", "payload": {}, "checksum": 999999}\n')

        # Write valid record 3
        wal.append_record(RecordType.TASK_COMMIT, {"task_id": "T1", "output": "ok"})

        # Run salvage
        salvage_res = recovery_engine.salvage_corrupted_wal(dag_id)
        assert salvage_res["status"] == "salvaged"
        assert salvage_res["valid_records_count"] == 2
        assert salvage_res["quarantined_records_count"] == 1

        # Check quarantine file was created
        quarantine_file = wal_dir / f"quarantine_dag_{dag_id}.bad"
        assert quarantine_file.exists()

        # Re-read records: should be 2 valid records without throwing Corrupt error
        records = wal.read_records()
        assert len(records) == 2
        assert records[0].record_type == RecordType.DAG_START
        assert records[1].record_type == RecordType.TASK_COMMIT
