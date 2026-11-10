"""Storage Quota Sentinel & Growth Management Engine for C.O.P.P.E.R.

Monitors physical file sizes of SQLite databases, ChromaDB vector collections,
and local file artifact caches, enforcing quotas and preventing disk exhaustion.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.core.logger import logger

DATA_DIR = Path(__file__).resolve().parent.parent.parent.parent / "data"


@dataclass(frozen=True)
class StorageQuotaStatus:
    total_used_mb: float
    quota_limit_mb: float
    utilization_pct: float
    is_warning: bool       # >= 80% quota
    is_critical: bool      # >= 95% quota
    directory_breakdown_mb: dict[str, float]


class StorageQuotaSentinel:
    """Monitors storage directory growth and enforces write admission quotas."""

    def __init__(self, quota_limit_mb: float = 5120.0, data_root: Path | None = None):
        self.quota_limit_mb = quota_limit_mb
        self.data_root = data_root or DATA_DIR

    def _get_dir_size_mb(self, path: Path) -> float:
        if not path.exists():
            return 0.0
        if path.is_file():
            return path.stat().st_size / (1024.0 * 1024.0)
        total_bytes = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_bytes += os.path.getsize(fp)
                except OSError:
                    pass
        return total_bytes / (1024.0 * 1024.0)

    def evaluate_storage_quota(self) -> StorageQuotaStatus:
        """Evaluates current physical disk consumption against allocated quota."""
        targets = {
            "sqlite_db": self.data_root / "copper_memory.db",
            "chroma_vectors": self.data_root / "chroma",
            "wal_logs": self.data_root / "wal",
            "images": self.data_root / "images",
            "documents": self.data_root / "documents",
        }

        breakdown = {name: round(self._get_dir_size_mb(p), 2) for name, p in targets.items()}
        total_used = round(sum(breakdown.values()), 2)
        util_pct = round((total_used / max(1.0, self.quota_limit_mb)) * 100.0, 1)

        is_warning = util_pct >= 80.0
        is_critical = util_pct >= 95.0

        if is_critical:
            logger.error(f"[StorageSentinel] CRITICAL: Storage usage is {total_used}MB ({util_pct}%) of {self.quota_limit_mb}MB quota.")
        elif is_warning:
            logger.warning(f"[StorageSentinel] WARNING: Storage usage is {total_used}MB ({util_pct}%) of {self.quota_limit_mb}MB quota.")

        return StorageQuotaStatus(
            total_used_mb=total_used,
            quota_limit_mb=self.quota_limit_mb,
            utilization_pct=util_pct,
            is_warning=is_warning,
            is_critical=is_critical,
            directory_breakdown_mb=breakdown,
        )

    def can_write_artifact(self, artifact_size_mb: float = 1.0) -> tuple[bool, str | None]:
        """Admission check before writing non-critical artifacts or documents."""
        status = self.evaluate_storage_quota()
        if (status.total_used_mb + artifact_size_mb) >= (self.quota_limit_mb * 0.95):
            return False, f"Storage quota exceeded: {status.total_used_mb:.1f}MB used out of {self.quota_limit_mb:.1f}MB."
        return True, None


storage_quota_sentinel = StorageQuotaSentinel()
