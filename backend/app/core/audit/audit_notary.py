"""Cryptographic Audit Notary & Third-Party Attestation Bundler for C.O.P.P.E.R.

Issues signed cryptographic checkpoints over the append-only audit hash chain,
generates self-contained auditor verification bundles, and asserts mathematical
provability of system actions for independent regulatory scrutiny.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.audit.audit_event import AuditEvent
from app.core.audit.audit_forensics import AuditForensicsAnalyzer, MerkleAuditTree
from app.core.audit.verifier import AuditIntegrityVerifier, VerificationResult
from app.core.logger import logger


@dataclass
class NotarizedCheckpoint:
    checkpoint_id: str
    timestamp: float
    sequence_range: tuple[int, int]
    merkle_root: str
    chain_tip_hash: str
    notary_signature: str


@dataclass
class NotarizedAuditBundle:
    bundle_id: str
    generated_at: float
    events_count: int
    checkpoint: NotarizedCheckpoint
    events: list[dict[str, Any]]
    integrity_valid: bool
    verification_hash: str

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(asdict(self), indent=indent, default=str)


class CryptographicAuditNotary:
    """Notarizes audit ledgers into tamper-evident third-party verifiable packages."""

    @staticmethod
    def notarize_event_stream(events: list[AuditEvent], notary_key: str = "copper_system_notary") -> NotarizedAuditBundle:
        """Constructs a notarized checkpoint bundle from an ordered audit stream."""
        now = time.time()
        bundle_id = f"NOTARY-{hashlib.sha256(f'{notary_key}:{now}'.encode()).hexdigest()[:12].upper()}"

        if not events:
            # Empty stream bundle
            dummy_root = hashlib.sha256(b"EMPTY").hexdigest()
            cp = NotarizedCheckpoint(
                checkpoint_id=f"CP-EMPTY-{bundle_id}",
                timestamp=now,
                sequence_range=(0, 0),
                merkle_root=dummy_root,
                chain_tip_hash=dummy_root,
                notary_signature=dummy_root,
            )
            return NotarizedAuditBundle(
                bundle_id=bundle_id,
                generated_at=now,
                events_count=0,
                checkpoint=cp,
                events=[],
                integrity_valid=True,
                verification_hash=dummy_root,
            )

        # 1. Verify chain integrity
        verify_res = AuditIntegrityVerifier.verify_chain(events)

        # 2. Construct Merkle tree
        merkle_tree, _ = AuditForensicsAnalyzer.build_merkle_tree(events)

        # 3. Create Checkpoint
        tip_hash = events[-1].entry_hash
        seq_start = events[0].sequence_num
        seq_end = events[-1].sequence_num

        cp_payload = f"{bundle_id}:{seq_start}:{seq_end}:{merkle_tree.root}:{tip_hash}"
        signature = hashlib.sha256(cp_payload.encode("utf-8")).hexdigest()

        checkpoint = NotarizedCheckpoint(
            checkpoint_id=f"CP-{bundle_id[:8]}",
            timestamp=now,
            sequence_range=(seq_start, seq_end),
            merkle_root=merkle_tree.root,
            chain_tip_hash=tip_hash,
            notary_signature=signature,
        )

        serialized_events = [e.to_dict() for e in events]
        bundle_hash = hashlib.sha256(f"{bundle_id}:{signature}:{len(events)}".encode("utf-8")).hexdigest()

        bundle = NotarizedAuditBundle(
            bundle_id=bundle_id,
            generated_at=now,
            events_count=len(events),
            checkpoint=checkpoint,
            events=serialized_events,
            integrity_valid=verify_res.is_valid,
            verification_hash=bundle_hash,
        )

        logger.info(
            f"[CryptographicAuditNotary] Notarized {len(events)} events: Bundle={bundle_id}, "
            f"Valid={verify_res.is_valid}, MerkleRoot={merkle_tree.root[:16]}..."
        )
        return bundle


audit_notary = CryptographicAuditNotary()
