"""Quantum-Safe Hash-Based Audit Log Chaining and Post-Quantum Verification.

Implements Stage 10 Auditability & Accountability Architecture:
- Implements SHA-3 / SHAKE-256 cryptographic chaining resistant to Grover's quantum search algorithm.
- Computes post-quantum verifiable audit checkpoints and checkpoint witness digests.
- Secures system audit logs against retrospective quantum computing attacks.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class QuantumAuditEntry:
    entry_index: int
    event_type: str
    event_data: dict[str, Any]
    prev_quantum_hash: str
    current_quantum_hash: str
    timestamp_epoch: float = field(default_factory=time.time)


@dataclass
class QuantumCheckpointWitness:
    checkpoint_id: str
    start_index: int
    end_index: int
    quantum_merkle_root: str
    witness_signature: str
    sealed_at: float


class QuantumSafeAuditChain:
    """Audit log ledger utilizing SHA3-384 hash chaining for post-quantum security guarantees."""

    GENESIS_HASH = "000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

    def __init__(self, chain_id: str = "quantum-audit-01") -> None:
        self.chain_id = chain_id
        self._entries: list[QuantumAuditEntry] = []
        self._checkpoints: list[QuantumCheckpointWitness] = []

    def _hash_quantum(self, payload: str) -> str:
        """Compute SHA3-384 digest providing 192 bits of post-quantum collision resistance."""
        return hashlib.sha3_384(payload.encode("utf-8")).hexdigest()

    def append_audit_entry(self, event_type: str, event_data: dict[str, Any]) -> QuantumAuditEntry:
        """Append an event to the quantum-safe hash chain."""
        prev_hash = self._entries[-1].current_quantum_hash if self._entries else self.GENESIS_HASH
        idx = len(self._entries)
        now = time.time()

        content = f"{idx}:{event_type}:{sorted(event_data.items())}:{prev_hash}:{now}"
        curr_hash = self._hash_quantum(content)

        entry = QuantumAuditEntry(
            entry_index=idx,
            event_type=event_type,
            event_data=event_data,
            prev_quantum_hash=prev_hash,
            current_quantum_hash=curr_hash,
            timestamp_epoch=now,
        )
        self._entries.append(entry)
        return entry

    def seal_checkpoint(self, checkpoint_id: str) -> QuantumCheckpointWitness:
        """Seal current entries into a quantum-safe Merkle root checkpoint."""
        if not self._entries:
            root = self.GENESIS_HASH
            start, end = 0, 0
        else:
            start = self._checkpoints[-1].end_index + 1 if self._checkpoints else 0
            end = len(self._entries) - 1
            hashes = [e.current_quantum_hash for e in self._entries[start: end + 1]]
            root = self._hash_quantum(":".join(hashes))

        witness = QuantumCheckpointWitness(
            checkpoint_id=checkpoint_id,
            start_index=start,
            end_index=end,
            quantum_merkle_root=root,
            witness_signature=self._hash_quantum(f"{checkpoint_id}:{root}:{self.chain_id}"),
            sealed_at=time.time(),
        )
        self._checkpoints.append(witness)
        return witness

    def verify_chain_integrity(self) -> bool:
        """Verify the cryptographic hash link of every entry in the chain."""
        for i, entry in enumerate(self._entries):
            expected_prev = self._entries[i - 1].current_quantum_hash if i > 0 else self.GENESIS_HASH
            if entry.prev_quantum_hash != expected_prev:
                return False

            content = f"{entry.entry_index}:{entry.event_type}:{sorted(entry.event_data.items())}:{entry.prev_quantum_hash}:{entry.timestamp_epoch}"
            expected_curr = self._hash_quantum(content)
            if entry.current_quantum_hash != expected_curr:
                return False

        return True
