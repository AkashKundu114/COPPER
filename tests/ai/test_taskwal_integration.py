import asyncio
import tempfile
from pathlib import Path

import pytest

from app.ai.orchestration.task_graph import TaskGraphExecutor
from app.ai.orchestration.planner import PlanResult, SubTask
from app.ai.orchestration.wal_executor import (
    CrashRecoveryEngine,
    RecordType,
    TaskWAL,
    current_task_id,
    current_wal,
)
from app.ai.tools.builtin.file_tools import file_write
from backend.eval.chaos_harness import ChaosHarness


@pytest.mark.asyncio
async def test_file_write_emits_mutation_record_under_active_wal():
    """Verify that file_write emits MUTATION_RECORD when running within an active TaskWAL context."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        wal = TaskWAL(dag_id="test_dag_mutation", wal_dir=tmp_path)
        test_file = tmp_path / "created_by_tool.txt"

        wal_tok = current_wal.set(wal)
        task_tok = current_task_id.set("T_WRITE_01")
        try:
            res = await file_write(str(test_file), "hello world from tool")
            assert res["status"] == "success"
            assert test_file.exists()
        finally:
            current_wal.reset(wal_tok)
            current_task_id.reset(task_tok)

        records = wal.read_records()
        mutation_records = [r for r in records if r.record_type == RecordType.MUTATION_RECORD]
        assert len(mutation_records) == 1
        assert mutation_records[0].payload["task_id"] == "T_WRITE_01"
        assert mutation_records[0].payload["type"] == "file_created"
        assert mutation_records[0].payload["path"] == str(test_file.resolve())


@pytest.mark.asyncio
async def test_file_write_records_pre_image_for_overwrite():
    """Verify that file_write records original content as pre-image before overwriting an existing file."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        wal = TaskWAL(dag_id="test_dag_overwrite", wal_dir=tmp_path)
        existing_file = tmp_path / "existing.txt"
        existing_file.write_text("initial baseline data", encoding="utf-8")

        wal_tok = current_wal.set(wal)
        task_tok = current_task_id.set("T_OVERWRITE_02")
        try:
            res = await file_write(str(existing_file), "new modified data", mode="overwrite")
            assert res["status"] == "success"
        finally:
            current_wal.reset(wal_tok)
            current_task_id.reset(task_tok)

        records = wal.read_records()
        mutations = [r for r in records if r.record_type == RecordType.MUTATION_RECORD]
        assert len(mutations) == 1
        assert mutations[0].payload["type"] == "file_modified"
        assert mutations[0].payload["pre_image"] == "initial baseline data"


def test_crash_recovery_engine_restores_pre_image():
    """Verify that CrashRecoveryEngine restores pre-image content upon uncommitted crash."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        engine = CrashRecoveryEngine(wal_dir=tmp_path)
        wal = TaskWAL(dag_id="dag_crash_restore", wal_dir=tmp_path)

        wal.append_record(RecordType.DAG_START, {"goal": "test restore"})
        file_to_modify = tmp_path / "doc.txt"
        file_to_modify.write_text("clean state before crash", encoding="utf-8")

        wal.append_record(
            RecordType.MUTATION_RECORD,
            {
                "task_id": "T1",
                "type": "file_modified",
                "path": str(file_to_modify),
                "pre_image": "clean state before crash",
            },
        )
        file_to_modify.write_text("corrupted uncommitted write", encoding="utf-8")

        rollbacks = engine.rollback_uncommitted_mutations("dag_crash_restore")
        assert rollbacks == 1
        assert file_to_modify.read_text(encoding="utf-8") == "clean state before crash"

        # Verify idempotency: repeated rollback does not re-modify or crash
        rollbacks_second = engine.rollback_uncommitted_mutations("dag_crash_restore")
        assert rollbacks_second == 0
        assert file_to_modify.read_text(encoding="utf-8") == "clean state before crash"


def test_scaled_500_trial_crash_recovery_statistical_bounds():
    """Execute 500 simulated crash recovery trials and verify 100% recovery with Clopper-Pearson >= 99.2%."""
    harness = ChaosHarness()
    results = harness.run_crash_recovery_test(num_trials=500)

    assert results["crashes_simulated"] == 500
    assert results["successful_recoveries"] == 500
    assert results["recovery_rate_pct"] == 100.0

    lower_ci, upper_ci = results["clopper_pearson_95_ci_pct"]
    assert lower_ci >= 99.20, f"Clopper-Pearson 95% lower bound {lower_ci}% below 99.20%"
    assert upper_ci == 100.0

    # Ensure all 5 failure modes were thoroughly exercised
    breakdown = results["fault_breakdown"]
    assert breakdown["file_created_unlinked"] == 100
    assert breakdown["file_modified_restored"] == 100
    assert breakdown["partial_commit_preserved"] == 100
    assert breakdown["truncated_crc_isolated"] == 100
    assert breakdown["idempotent_re_recovery"] == 100
