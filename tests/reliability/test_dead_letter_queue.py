import tempfile
from pathlib import Path
import pytest

from app.core.resilience.dead_letter_queue import DeadLetterQueue


def test_dead_letter_queue_lifecycle():
    """Verify DLQ persists, lists, marks replayed, and purges unrecoverable records."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dlq = DeadLetterQueue(dlq_dir=Path(tmpdir))

        # Enqueue poisoned tasks
        r1 = dlq.enqueue(
            task_id="task_fail_1",
            origin_service="coding_agent",
            failure_reason="SyntaxError in generated AST",
            payload={"code": "def bad_syntax(:", "attempts": 3},
            error_type="SyntaxError",
            attempts_count=3,
        )
        r2 = dlq.enqueue(
            task_id="task_fail_2",
            origin_service="document_agent",
            failure_reason="Corrupted PDF bytes",
            payload={"doc_id": "pdf-123"},
            error_type="PDFSyntaxError",
            attempts_count=2,
        )

        assert r1.task_id == "task_fail_1"
        assert r2.task_id == "task_fail_2"

        # List active records
        records = dlq.list_records(include_replayed=False)
        assert len(records) == 2
        assert records[0].task_id == "task_fail_1"
        assert records[1].task_id == "task_fail_2"

        # Mark first as replayed
        success = dlq.mark_replayed(r1.record_id)
        assert success is True

        # Now only 1 active record remains
        active_records = dlq.list_records(include_replayed=False)
        assert len(active_records) == 1
        assert active_records[0].task_id == "task_fail_2"

        # Purge replayed
        purged_count = dlq.purge_replayed()
        assert purged_count == 1

        all_records = dlq.list_records(include_replayed=True)
        assert len(all_records) == 1
        assert all_records[0].task_id == "task_fail_2"
