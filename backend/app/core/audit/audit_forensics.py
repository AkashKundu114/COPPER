"""Merkle Tree Inclusion Proof & Chronological Forensics Analyzer for C.O.P.P.E.R.

Builds binary Merkle Trees over append-only audit event ledgers, generates mathematical
inclusion proofs for individual events, and performs causal chain forensics to detect
out-of-order execution, dropped events, or sequence anomalies.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.audit.audit_event import AuditEvent
from app.core.logger import logger


@dataclass
class MerkleInclusionProof:
    event_id: str
    leaf_hash: str
    leaf_index: int
    proof_path: list[tuple[str, str]]  # [(sibling_hash, "left"|"right")]
    merkle_root: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CausalTraceNode:
    sequence_num: int
    event_id: str
    timestamp: float
    actor: str
    action: str
    outcome: str
    parent_event_id: str | None = None


@dataclass
class ForensicAnalysisReport:
    report_id: str
    timestamp: float
    total_events_analyzed: int
    merkle_root: str
    sequence_intact: bool
    chronology_intact: bool
    detected_gaps: list[int]
    detected_inversions: list[str]
    causal_trace: list[CausalTraceNode]
    is_valid_forensic_chain: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _hash_pair(left: str, right: str) -> str:
    """Computes SHA-256 parent node hash from two child hashes."""
    combined = f"{left}:{right}".encode("utf-8")
    return hashlib.sha256(combined).hexdigest()


class MerkleAuditTree:
    """Binary Merkle Tree for batch audit event integrity and inclusion proofs."""

    def __init__(self, leaf_hashes: list[str]):
        if not leaf_hashes:
            self.root = hashlib.sha256(b"EMPTY_MERKLE_TREE").hexdigest()
            self.levels: list[list[str]] = [[]]
            return

        self.levels = [leaf_hashes]
        current = leaf_hashes

        while len(current) > 1:
            next_level = []
            for i in range(0, len(current), 2):
                left = current[i]
                right = current[i + 1] if i + 1 < len(current) else current[i]
                next_level.append(_hash_pair(left, right))
            self.levels.append(next_level)
            current = next_level

        self.root = current[0]

    def generate_proof(self, leaf_index: int) -> list[tuple[str, str]]:
        """Generates sibling authentication path for a leaf index."""
        if not self.levels or not self.levels[0] or leaf_index >= len(self.levels[0]):
            return []

        proof: list[tuple[str, str]] = []
        idx = leaf_index

        for level in self.levels[:-1]:
            is_right_child = (idx % 2 == 1)
            sibling_idx = idx - 1 if is_right_child else idx + 1

            if sibling_idx < len(level):
                sibling_hash = level[sibling_idx]
            else:
                sibling_hash = level[idx]  # Duplicated rightmost leaf

            direction = "left" if is_right_child else "right"
            proof.append((sibling_hash, direction))
            idx //= 2

        return proof

    @staticmethod
    def verify_proof(leaf_hash: str, proof: list[tuple[str, str]], expected_root: str) -> bool:
        """Mathematically verifies that a leaf belongs to the Merkle tree with the given root."""
        current = leaf_hash
        for sibling_hash, direction in proof:
            if direction == "left":
                current = _hash_pair(sibling_hash, current)
            else:
                current = _hash_pair(current, sibling_hash)
        return current == expected_root


class AuditForensicsAnalyzer:
    """Forensic investigation engine analyzing audit logs and event chains."""

    @staticmethod
    def build_merkle_tree(events: list[AuditEvent]) -> tuple[MerkleAuditTree, dict[str, int]]:
        """Constructs a Merkle tree over the event hash sequence."""
        leaf_hashes = [e.entry_hash for e in events]
        event_indices = {e.event_id: idx for idx, e in enumerate(events)}
        return MerkleAuditTree(leaf_hashes), event_indices

    @staticmethod
    def create_inclusion_proof(events: list[AuditEvent], event_id: str) -> MerkleInclusionProof | None:
        """Creates a verifiable Merkle inclusion proof for a target event."""
        tree, event_map = AuditForensicsAnalyzer.build_merkle_tree(events)
        if event_id not in event_map:
            return None

        idx = event_map[event_id]
        event = events[idx]
        proof_path = tree.generate_proof(idx)

        return MerkleInclusionProof(
            event_id=event.event_id,
            leaf_hash=event.entry_hash,
            leaf_index=idx,
            proof_path=proof_path,
            merkle_root=tree.root,
        )

    @staticmethod
    def analyze_chronology_and_causality(events: list[AuditEvent]) -> ForensicAnalysisReport:
        """Analyzes event timestamps and sequence numbers for forensic integrity."""
        tree, _ = AuditForensicsAnalyzer.build_merkle_tree(events)

        gaps: list[int] = []
        inversions: list[str] = []
        causal_trace: list[CausalTraceNode] = []

        prev_seq: int | None = None
        prev_time: float | None = None
        prev_id: str | None = None

        for e in events:
            # Check sequence continuity
            if prev_seq is not None:
                if e.sequence_num != prev_seq + 1:
                    gaps.append(e.sequence_num)

            # Check timestamp monotonicity (allow 0.05s tolerance for clock jitter)
            if prev_time is not None:
                if e.timestamp < (prev_time - 0.05):
                    inversions.append(f"Event {e.event_id} timestamp {e.timestamp} < prev {prev_time}")

            causal_trace.append(
                CausalTraceNode(
                    sequence_num=e.sequence_num,
                    event_id=e.event_id,
                    timestamp=e.timestamp,
                    actor=e.actor,
                    action=e.action,
                    outcome=e.outcome.value if hasattr(e.outcome, "value") else str(e.outcome),
                    parent_event_id=prev_id,
                )
            )

            prev_seq = e.sequence_num
            prev_time = e.timestamp
            prev_id = e.event_id

        seq_intact = len(gaps) == 0
        chrono_intact = len(inversions) == 0
        is_valid = seq_intact and chrono_intact and len(events) > 0

        ts = time.time()
        report_id = f"FORENSIC-{hashlib.sha256(str(ts).encode()).hexdigest()[:12].upper()}"

        return ForensicAnalysisReport(
            report_id=report_id,
            timestamp=ts,
            total_events_analyzed=len(events),
            merkle_root=tree.root,
            sequence_intact=seq_intact,
            chronology_intact=chrono_intact,
            detected_gaps=gaps,
            detected_inversions=inversions,
            causal_trace=causal_trace,
            is_valid_forensic_chain=is_valid,
        )


audit_forensics = AuditForensicsAnalyzer()
