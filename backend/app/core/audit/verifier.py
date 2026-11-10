"""Cryptographic Audit Chain Integrity Verifier for C.O.P.P.E.R.

Traverses append-only audit event streams, validates SHA-256 hash chains,
detects missing sequence numbers, payload tampering, and unverified blocks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.audit.audit_event import AuditEvent, GENESIS_HASH
from app.core.logger import logger


@dataclass
class VerificationResult:
    is_valid: bool
    verified_events_count: int
    corrupted_event_id: str | None = None
    corrupted_sequence_num: int | None = None
    error_message: str | None = None
    chain_tip_hash: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


class AuditIntegrityVerifier:
    """Validates cryptographic integrity and immutability of the audit chain."""

    @staticmethod
    def verify_chain(events: list[AuditEvent]) -> VerificationResult:
        if not events:
            return VerificationResult(
                is_valid=True,
                verified_events_count=0,
                error_message="Audit log is empty; no events to verify.",
            )

        # 1. Verify Genesis Block (Sequence 0)
        first_event = events[0]
        if first_event.sequence_num != 0:
            return VerificationResult(
                is_valid=False,
                verified_events_count=0,
                corrupted_event_id=first_event.event_id,
                corrupted_sequence_num=first_event.sequence_num,
                error_message=f"Missing Genesis block: first event sequence is {first_event.sequence_num} instead of 0.",
            )

        if first_event.prev_hash != GENESIS_HASH:
            return VerificationResult(
                is_valid=False,
                verified_events_count=0,
                corrupted_event_id=first_event.event_id,
                corrupted_sequence_num=0,
                error_message=f"Corrupt Genesis block: prev_hash ({first_event.prev_hash[:16]}...) does not match standard genesis.",
            )

        expected_genesis_hash = first_event.calculate_entry_hash()
        if first_event.entry_hash != expected_genesis_hash:
            return VerificationResult(
                is_valid=False,
                verified_events_count=0,
                corrupted_event_id=first_event.event_id,
                corrupted_sequence_num=0,
                error_message="Genesis block entry_hash signature mismatch; payload has been tampered with.",
            )

        # 2. Iterate and verify chained blocks
        last_hash = first_event.entry_hash
        for idx in range(1, len(events)):
            current = events[idx]
            expected_seq = events[idx - 1].sequence_num + 1

            # Sequence Continuity Check
            if current.sequence_num != expected_seq:
                return VerificationResult(
                    is_valid=False,
                    verified_events_count=idx,
                    corrupted_event_id=current.event_id,
                    corrupted_sequence_num=current.sequence_num,
                    error_message=f"Audit chain sequence break: expected seq {expected_seq}, got {current.sequence_num}.",
                )

            # Predecessor Hash Pointer Check
            if current.prev_hash != last_hash:
                return VerificationResult(
                    is_valid=False,
                    verified_events_count=idx,
                    corrupted_event_id=current.event_id,
                    corrupted_sequence_num=current.sequence_num,
                    error_message=f"Hash chain broken at seq {current.sequence_num}: prev_hash does not match predecessor entry_hash.",
                )

            # Block Payload Integrity Check
            expected_entry_hash = current.calculate_entry_hash()
            if current.entry_hash != expected_entry_hash:
                return VerificationResult(
                    is_valid=False,
                    verified_events_count=idx,
                    corrupted_event_id=current.event_id,
                    corrupted_sequence_num=current.sequence_num,
                    error_message=f"Payload tampering detected at seq {current.sequence_num} ({current.event_id}).",
                )

            last_hash = current.entry_hash

        logger.info(f"[AuditVerifier] Successfully verified {len(events)} cryptographically chained audit events.")
        return VerificationResult(
            is_valid=True,
            verified_events_count=len(events),
            chain_tip_hash=last_hash,
            error_message=None,
        )


audit_verifier = AuditIntegrityVerifier()
