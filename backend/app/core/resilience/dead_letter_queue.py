"""Persistent Dead-Letter Queue (DLQ) for Unrecoverable Task Payloads."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.core.logger import logger

DEFAULT_DLQ_DIR = Path(__file__).parent.parent.parent.parent / "data" / "dlq"


@dataclass
class DLQRecord:
    record_id: str
    task_id: str
    origin_service: str
    failure_reason: str
    error_type: str
    payload: dict[str, Any]
    attempts_count: int
    timestamp: float = field(default_factory=time.time)
    replayed: bool = False
    replayed_at: float | None = None

    def to_json_line(self) -> str:
        return json.dumps(asdict(self)) + "\n"

    @classmethod
    def from_json_line(cls, line: str) -> DLQRecord:
        data = json.loads(line)
        return cls(**data)


class DeadLetterQueue:
    """Persistent local-first Dead-Letter Queue."""

    def __init__(self, dlq_dir: Path | None = None):
        self.dlq_dir = dlq_dir or DEFAULT_DLQ_DIR
        self.dlq_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.dlq_dir / "dlq_records.jsonl"

    def enqueue(
        self,
        task_id: str,
        origin_service: str,
        failure_reason: str,
        payload: dict[str, Any],
        error_type: str = "UnhandledExecutionError",
        attempts_count: int = 1,
    ) -> DLQRecord:
        import uuid

        record = DLQRecord(
            record_id=str(uuid.uuid4()),
            task_id=task_id,
            origin_service=origin_service,
            failure_reason=str(failure_reason),
            error_type=error_type,
            payload=payload,
            attempts_count=attempts_count,
        )

        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(record.to_json_line())

        logger.warning(
            f"[DLQ] Enqueued poisoned/unrecoverable task {task_id} from {origin_service}: {failure_reason}"
        )
        return record

    def list_records(self, include_replayed: bool = False, limit: int = 100) -> list[DLQRecord]:
        if not self.file_path.exists():
            return []

        records = []
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = DLQRecord.from_json_line(line)
                    if not rec.replayed or include_replayed:
                        records.append(rec)
                except Exception as e:
                    logger.error(f"[DLQ] Corrupted record skipped: {e}")

        return records[-limit:]

    def mark_replayed(self, record_id: str) -> bool:
        if not self.file_path.exists():
            return False

        all_records = []
        found = False
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = DLQRecord.from_json_line(line)
                    if rec.record_id == record_id:
                        rec.replayed = True
                        rec.replayed_at = time.time()
                        found = True
                    all_records.append(rec)
                except Exception:
                    pass

        if found:
            with open(self.file_path, "w", encoding="utf-8") as f:
                for rec in all_records:
                    f.write(rec.to_json_line())
        return found

    def purge_replayed(self) -> int:
        if not self.file_path.exists():
            return 0

        active = []
        purged = 0
        with open(self.file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = DLQRecord.from_json_line(line)
                    if rec.replayed:
                        purged += 1
                    else:
                        active.append(rec)
                except Exception:
                    pass

        with open(self.file_path, "w", encoding="utf-8") as f:
            for rec in active:
                f.write(rec.to_json_line())
        return purged


dead_letter_queue = DeadLetterQueue()
