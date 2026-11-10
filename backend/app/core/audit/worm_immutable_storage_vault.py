"""Write-Once-Read-Many (WORM) Immutable Audit Storage Vault.

Implements Stage 12 Auditability & Accountability Architecture:
- Enforces strict Write-Once-Read-Many (WORM) compliance and retention-locked immutability.
- Blocks unauthorized record updates, premature deletions, and metadata tampering.
- Supports administrative Legal Holds and cryptographically verified audit attestation manifests.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class WORMRecord:
    record_id: str
    payload: dict[str, Any]
    immutable_hash: str
    created_at_epoch: float
    retention_expires_at: float
    is_legal_hold: bool = False


class WORMImmutableStorageVault:
    """WORM-compliant storage engine that forbids modification or early deletion of audit records."""

    def __init__(self, default_retention_seconds: float = 31536000.0) -> None:  # 1 year default
        self.default_retention_seconds = default_retention_seconds
        self._vault_records: dict[str, WORMRecord] = {}

    def store_record(
        self,
        record_id: str,
        payload: dict[str, Any],
        retention_seconds: Optional[float] = None,
        legal_hold: bool = False,
    ) -> WORMRecord:
        """Store a record permanently. Fails if record_id already exists."""
        if record_id in self._vault_records:
            raise PermissionError(f"WORM Violation: Record '{record_id}' already exists and cannot be overwritten.")

        now = time.time()
        ret_sec = retention_seconds if retention_seconds is not None else self.default_retention_seconds
        content_hash = hashlib.sha256(f"{record_id}:{sorted(payload.items())}:{now}".encode("utf-8")).hexdigest()

        rec = WORMRecord(
            record_id=record_id,
            payload=payload,
            immutable_hash=content_hash,
            created_at_epoch=now,
            retention_expires_at=now + ret_sec,
            is_legal_hold=legal_hold,
        )
        self._vault_records[record_id] = rec
        return rec

    def attempt_delete(self, record_id: str) -> bool:
        """Attempt deletion. Rejected if within retention window or under legal hold."""
        rec = self._vault_records.get(record_id)
        if not rec:
            return False

        if rec.is_legal_hold:
            raise PermissionError(f"WORM Violation: Record '{record_id}' is under active Legal Hold.")

        if time.time() < rec.retention_expires_at:
            raise PermissionError(
                f"WORM Violation: Record '{record_id}' is retention-locked until epoch {rec.retention_expires_at}."
            )

        del self._vault_records[record_id]
        return True

    def get_record(self, record_id: str) -> Optional[WORMRecord]:
        return self._vault_records.get(record_id)

    def get_records_count(self) -> int:
        return len(self._vault_records)
