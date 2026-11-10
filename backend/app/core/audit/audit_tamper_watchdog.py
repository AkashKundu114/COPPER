"""Continuous Audit Tamper Detection & Ledger Integrity Watchdog for C.O.P.P.E.R.

Actively scans append-only audit logs, validates cryptographic hash continuity across
chained event blocks, detects backdated injection or omission attacks, and produces
tamper-evident forensic inspection certificates.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.audit.audit_event import AuditEvent, GENESIS_HASH
from app.core.audit.verifier import AuditIntegrityVerifier, VerificationResult
from app.core.logger import logger


@dataclass
class AuditTamperInspectionReport:
    inspection_id: str
    timestamp: float
    events_scanned: int
    chain_intact: bool
    tamper_detected: bool
    corrupted_event_id: str | None
    genesis_valid: bool
    chain_tip_hash: str
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AuditTamperWatchdog:
    """Watchdog continuously auditing the cryptographic hash chain for tampering."""

    @staticmethod
    def inspect_ledger_chain(events: list[AuditEvent]) -> AuditTamperInspectionReport:
        """Verifies full cryptographic continuity and sequence integrity across all blocks."""
        now = time.time()
        insp_id = f"ATW-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"

        if not events:
            dummy_hash = hashlib.sha256(b"EMPTY_LEDGER").hexdigest()
            return AuditTamperInspectionReport(
                inspection_id=insp_id,
                timestamp=now,
                events_scanned=0,
                chain_intact=True,
                tamper_detected=False,
                corrupted_event_id=None,
                genesis_valid=True,
                chain_tip_hash=dummy_hash,
                signature=dummy_hash,
            )

        # 1. Run core verifier
        verify_result = AuditIntegrityVerifier.verify_chain(events)

        # 2. Check Genesis Block
        first = events[0]
        genesis_ok = (first.sequence_num == 0) and (first.prev_hash == GENESIS_HASH)

        chain_tip = events[-1].entry_hash
        sig = hashlib.sha256(f"{insp_id}:{verify_result.is_valid}:{len(events)}:{chain_tip}".encode()).hexdigest()

        report = AuditTamperInspectionReport(
            inspection_id=insp_id,
            timestamp=now,
            events_scanned=len(events),
            chain_intact=verify_result.is_valid,
            tamper_detected=not verify_result.is_valid,
            corrupted_event_id=verify_result.corrupted_event_id,
            genesis_valid=genesis_ok,
            chain_tip_hash=chain_tip,
            signature=sig,
        )

        logger.info(
            f"[AuditTamperWatchdog] Inspection completed: Scanned={len(events)}, "
            f"ChainIntact={verify_result.is_valid}, TamperDetected={not verify_result.is_valid}"
        )
        return report


audit_tamper_watchdog = AuditTamperWatchdog()
