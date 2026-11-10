"""Crash-Consistent Write-Ahead Log (WAL) & Idempotent Checkpoint Engine."""

import contextvars
import hashlib
import json
import os
import time
import zlib
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from app.core.logger import logger

DEFAULT_WAL_DIR = Path(__file__).parent.parent.parent.parent / "data" / "wal"

current_wal: contextvars.ContextVar[Any | None] = contextvars.ContextVar("current_wal", default=None)
current_task_id: contextvars.ContextVar[str | None] = contextvars.ContextVar("current_task_id", default=None)


class RecordType(str, Enum):
    DAG_START = "DAG_START"
    TASK_INTENT = "TASK_INTENT"
    MUTATION_RECORD = "MUTATION_RECORD"
    TASK_COMMIT = "TASK_COMMIT"
    TASK_FAIL = "TASK_FAIL"
    TASK_COMPENSATE = "TASK_COMPENSATE"
    DAG_RESUME = "DAG_RESUME"
    DAG_COMMIT = "DAG_COMMIT"
    DAG_ABORT = "DAG_ABORT"


@dataclass
class WALRecord:
    seq_num: int
    timestamp: float
    dag_id: str
    record_type: RecordType
    payload: dict[str, Any]
    checksum: int = 0

    def calculate_checksum(self) -> int:
        raw = f"{self.seq_num}:{self.timestamp}:{self.dag_id}:{self.record_type}:{json.dumps(self.payload, sort_keys=True)}"
        return zlib.crc32(raw.encode("utf-8"))

    def to_json_line(self) -> str:
        self.checksum = self.calculate_checksum()
        data = asdict(self)
        data["record_type"] = self.record_type.value
        return json.dumps(data) + "\n"

    @classmethod
    def from_json_line(cls, line: str) -> "WALRecord":
        obj = json.loads(line)
        rec = cls(
            seq_num=obj["seq_num"],
            timestamp=obj["timestamp"],
            dag_id=obj["dag_id"],
            record_type=RecordType(obj["record_type"]),
            payload=obj["payload"],
            checksum=obj["checksum"],
        )
        expected = rec.calculate_checksum()
        if rec.checksum != expected:
            raise ValueError(
                f"Corrupt WAL entry detected at seq {rec.seq_num}: checksum mismatch ({rec.checksum} != {expected})"
            )
        return rec


class TaskWAL:
    """Append-only WAL manager for a single DAG run."""

    def __init__(self, dag_id: str, wal_dir: Path | None = None):
        self.dag_id = dag_id
        self.wal_dir = wal_dir or DEFAULT_WAL_DIR
        self.wal_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.wal_dir / f"dag_{self.dag_id}.wal"
        self._seq_counter = 0

    def append_record(self, record_type: RecordType, payload: dict[str, Any]) -> WALRecord:
        self._seq_counter += 1
        record = WALRecord(
            seq_num=self._seq_counter,
            timestamp=time.time(),
            dag_id=self.dag_id,
            record_type=record_type,
            payload=payload,
        )
        line = record.to_json_line()
        with open(self.file_path, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()
            os.fsync(f.fileno())
        return record

    def read_records(self) -> list[WALRecord]:
        if not self.file_path.exists():
            return []
        records = []
        with open(self.file_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(WALRecord.from_json_line(line))
                except Exception as e:
                    logger.error(f"[WAL] Corrupted record skipped in {self.file_path}: {e}")
        return records


class CrashRecoveryEngine:
    """ARIES-inspired Recovery Engine:"""

    def __init__(self, wal_dir: Path | None = None):
        self.wal_dir = wal_dir or DEFAULT_WAL_DIR
        self.wal_dir.mkdir(parents=True, exist_ok=True)

    def generate_idempotency_key(self, dag_id: str, task_id: str, instruction: str) -> str:
        raw = f"{dag_id}:{task_id}:{instruction.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def find_incomplete_dags(self) -> list[str]:
        """Scans for WAL files that have DAG_START but lack DAG_COMMIT or DAG_ABORT."""
        incomplete = []
        for file in self.wal_dir.glob("dag_*.wal"):
            dag_id = file.stem.removeprefix("dag_")
            wal = TaskWAL(dag_id=dag_id, wal_dir=self.wal_dir)
            records = wal.read_records()
            if not records:
                continue

            has_start = any(r.record_type == RecordType.DAG_START for r in records)
            has_terminal = any(r.record_type in (RecordType.DAG_COMMIT, RecordType.DAG_ABORT) for r in records)

            if has_start and not has_terminal:
                incomplete.append(wal.dag_id)
        return incomplete

    def analyze_dag_state(self, dag_id: str) -> dict[str, Any]:
        """Reconstructs the execution state of an interrupted DAG:"""
        wal = TaskWAL(dag_id=dag_id, wal_dir=self.wal_dir)
        records = wal.read_records()

        committed_tasks: dict[str, Any] = {}
        pending_mutations: list[dict[str, Any]] = []
        is_complete = False

        for r in records:
            if r.record_type in (RecordType.DAG_COMMIT, RecordType.DAG_ABORT):
                is_complete = True
            elif r.record_type == RecordType.TASK_COMMIT:
                t_id = r.payload.get("task_id")
                committed_tasks[t_id] = r.payload.get("output")
                pending_mutations = [m for m in pending_mutations if m.get("task_id") != t_id]
            elif r.record_type == RecordType.MUTATION_RECORD:
                pending_mutations.append(r.payload)
            elif r.record_type == RecordType.TASK_COMPENSATE:
                comp_task = r.payload.get("task_id")
                comp_path = r.payload.get("path")
                pending_mutations = [
                    m
                    for m in pending_mutations
                    if not (m.get("task_id") == comp_task and (not comp_path or m.get("path") == comp_path))
                ]

        return {
            "dag_id": dag_id,
            "is_complete": is_complete,
            "committed_tasks": committed_tasks,
            "uncommitted_mutations": pending_mutations,
            "total_records": len(records),
        }

    def rollback_uncommitted_mutations(self, dag_id: str) -> int:
        """Compensates (rolls back) uncommitted side effects."""
        wal = TaskWAL(dag_id=dag_id, wal_dir=self.wal_dir)
        analysis = self.analyze_dag_state(dag_id)
        if analysis["is_complete"] or not analysis["uncommitted_mutations"]:
            return 0
        rollbacks_performed = 0

        for mut in analysis["uncommitted_mutations"]:
            mut_type = mut.get("type")
            path_str = mut.get("path")
            if mut_type == "file_created" and path_str:
                p = Path(path_str)
                if p.exists():
                    try:
                        p.unlink()
                        rollbacks_performed += 1
                        wal.append_record(
                            RecordType.TASK_COMPENSATE,
                            {"task_id": mut.get("task_id"), "action": "deleted_file", "path": path_str},
                        )
                        logger.info(f"[RecoveryEngine] Rolled back orphaned file: {path_str}")
                    except Exception as e:
                        logger.error(f"[RecoveryEngine] Rollback failed for {path_str}: {e}")
            elif mut_type == "file_modified" and path_str:
                p = Path(path_str)
                pre_image = mut.get("pre_image")
                try:
                    if pre_image is not None:
                        p.write_text(pre_image, encoding="utf-8")
                        rollbacks_performed += 1
                        wal.append_record(
                            RecordType.TASK_COMPENSATE,
                            {"task_id": mut.get("task_id"), "action": "restored_file", "path": path_str},
                        )
                        logger.info(f"[RecoveryEngine] Restored modified file: {path_str}")
                except Exception as e:
                    logger.error(f"[RecoveryEngine] Restore failed for {path_str}: {e}")

        wal.append_record(RecordType.DAG_ABORT, {"reason": "crash_rollback_completed"})
        return rollbacks_performed



    def can_resume_dag(self, dag_id: str) -> bool:
        """Determines whether an interrupted DAG has recoverable progress."""
        analysis = self.analyze_dag_state(dag_id)
        return not analysis["is_complete"] and bool(analysis["committed_tasks"])

    def prepare_dag_resumption(self, dag_id: str) -> dict[str, Any]:
        """Compensates any uncommitted in-flight mutations, preserves committed results,
        and logs a DAG_RESUME checkpoint record for safe replay.
        """
        wal = TaskWAL(dag_id=dag_id, wal_dir=self.wal_dir)
        analysis = self.analyze_dag_state(dag_id)
        if analysis["is_complete"]:
            return {"resumable": False, "reason": "DAG already completed or aborted"}

        # Compensate only uncommitted in-flight mutations
        compensated = 0
        for mut in analysis["uncommitted_mutations"]:
            mut_type = mut.get("type")
            path_str = mut.get("path")
            if mut_type == "file_created" and path_str:
                p = Path(path_str)
                if p.exists():
                    try:
                        p.unlink()
                        compensated += 1
                        wal.append_record(
                            RecordType.TASK_COMPENSATE,
                            {"task_id": mut.get("task_id"), "action": "deleted_file", "path": path_str},
                        )
                    except Exception as e:
                        logger.error(f"[RecoveryEngine] Compensation failed for {path_str}: {e}")
            elif mut_type == "file_modified" and path_str:
                p = Path(path_str)
                pre_image = mut.get("pre_image")
                if pre_image is not None:
                    try:
                        p.write_text(pre_image, encoding="utf-8")
                        compensated += 1
                        wal.append_record(
                            RecordType.TASK_COMPENSATE,
                            {"task_id": mut.get("task_id"), "action": "restored_file", "path": path_str},
                        )
                    except Exception as e:
                        logger.error(f"[RecoveryEngine] Compensation restore failed for {path_str}: {e}")

        wal.append_record(
            RecordType.DAG_RESUME,
            {
                "resumed_at": time.time(),
                "completed_tasks_count": len(analysis["committed_tasks"]),
                "compensated_mutations": compensated,
            },
        )

        return {
            "resumable": True,
            "dag_id": dag_id,
            "committed_tasks": analysis["committed_tasks"],
            "completed_task_ids": list(analysis["committed_tasks"].keys()),
            "compensated_mutations_count": compensated,
        }

    def salvage_corrupted_wal(self, dag_id: str) -> dict[str, Any]:
        """Recovers all valid records from a damaged WAL file, quarantining corrupted lines."""
        wal = TaskWAL(dag_id=dag_id, wal_dir=self.wal_dir)
        if not wal.file_path.exists():
            return {"status": "not_found"}

        valid_records: list[str] = []
        corrupted_lines: list[str] = []

        with open(wal.file_path, "r", encoding="utf-8") as f:
            for line in f:
                s = line.strip()
                if not s:
                    continue
                try:
                    WALRecord.from_json_line(s)
                    valid_records.append(s)
                except Exception as e:
                    corrupted_lines.append(s)

        if corrupted_lines:
            quarantine_path = self.wal_dir / f"quarantine_dag_{dag_id}.bad"
            with open(quarantine_path, "a", encoding="utf-8") as qf:
                for cl in corrupted_lines:
                    qf.write(cl + "\n")

            with open(wal.file_path, "w", encoding="utf-8") as vf:
                for vr in valid_records:
                    vf.write(vr + "\n")

        return {
            "status": "salvaged" if corrupted_lines else "intact",
            "valid_records_count": len(valid_records),
            "quarantined_records_count": len(corrupted_lines),
        }


crash_recovery_engine = CrashRecoveryEngine()
