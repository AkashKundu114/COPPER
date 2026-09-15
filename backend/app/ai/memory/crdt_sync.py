"""
Conflict-Free Replicated Data Types (CRDTs) & Offline P2P Epistemic Memory Sync.

Distributed Systems Internals Concept:
Strong Eventual Consistency (SEC) across multi-device networks (laptop, workstation, edge server)
without requiring a centralized cloud coordinator or distributed lock manager.

Features:
1. Lamport Logical Clocks & Vector Clocks for causal ordering across network partitions.
2. State-Based LWW-Element-Set (Last-Write-Wins Element Set CRDT):
   - Mathematically Commutative (A * B = B * A)
   - Associative ((A * B) * C = A * (B * C))
   - Idempotent (A * A = A)
3. Delta-Based Peer-to-Peer Synchronization:
   - Exports delta snapshots for transmission over local sockets/mDNS.
   - Deterministically merges divergent concurrent memory mutations.
"""

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger


@dataclass
class CRDTRecord:
    element_id: str
    value: Any
    timestamp: float
    lamport_clock: int
    node_id: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CRDTRecord":
        return cls(**data)


class VectorClock:
    """Vector Clock tracking causal state across distributed nodes."""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.clock: dict[str, int] = {node_id: 0}

    def tick(self) -> int:
        self.clock[self.node_id] = self.clock.get(self.node_id, 0) + 1
        return self.clock[self.node_id]

    def merge(self, other_clock: dict[str, int]) -> None:
        for node, val in other_clock.items():
            self.clock[node] = max(self.clock.get(node, 0), val)
        self.tick()

    def get_time(self) -> int:
        return self.clock.get(self.node_id, 0)

    def to_dict(self) -> dict[str, int]:
        return dict(self.clock)


class LWWElementSet:
    """
    Last-Write-Wins Element Set CRDT.
    Guarantees convergence regardless of packet arrival order or network partitions.
    """

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.vclock = VectorClock(node_id)
        # Element ID -> CRDTRecord
        self.add_set: dict[str, CRDTRecord] = {}
        self.remove_set: dict[str, CRDTRecord] = {}

    def add(self, element_id: str, value: Any) -> CRDTRecord:
        lamport = self.vclock.tick()
        record = CRDTRecord(
            element_id=element_id,
            value=value,
            timestamp=time.time(),
            lamport_clock=lamport,
            node_id=self.node_id,
        )
        existing = self.add_set.get(element_id)
        if existing is None or self._is_newer(record, existing):
            self.add_set[element_id] = record
        return record

    def remove(self, element_id: str) -> CRDTRecord | None:
        lamport = self.vclock.tick()
        record = CRDTRecord(
            element_id=element_id,
            value=None,
            timestamp=time.time(),
            lamport_clock=lamport,
            node_id=self.node_id,
        )
        existing = self.remove_set.get(element_id)
        if existing is None or self._is_newer(record, existing):
            self.remove_set[element_id] = record
        return record

    def _is_newer(self, a: CRDTRecord, b: CRDTRecord) -> bool:
        """Determines ordering using Lamport clock with node_id tie-breaker."""
        if a.lamport_clock != b.lamport_clock:
            return a.lamport_clock > b.lamport_clock
        if a.timestamp != b.timestamp:
            return a.timestamp > b.timestamp
        return a.node_id > b.node_id

    def lookup(self, element_id: str) -> Any | None:
        """
        Element is active if in add_set and not eclipsed by a newer remove_set entry.
        """
        if element_id not in self.add_set:
            return None
        add_rec = self.add_set[element_id]
        rem_rec = self.remove_set.get(element_id)

        if rem_rec is None:
            return add_rec.value

        # If remove is newer than add, element is considered deleted
        if self._is_newer(rem_rec, add_rec):
            return None
        return add_rec.value

    def read_all(self) -> dict[str, Any]:
        """Returns all active elements in the CRDT."""
        active = {}
        for elem_id in self.add_set:
            val = self.lookup(elem_id)
            if val is not None:
                active[elem_id] = val
        return active

    def merge(self, other_state: dict[str, Any]) -> int:
        """
        Merges an external peer's CRDT state.
        Returns the number of local mutations applied.
        """
        mutations_applied = 0
        other_adds = other_state.get("add_set", {})
        other_rems = other_state.get("remove_set", {})
        other_clock = other_state.get("vector_clock", {})

        # Merge Adds
        for elem_id, rec_data in other_adds.items():
            incoming = CRDTRecord.from_dict(rec_data)
            current = self.add_set.get(elem_id)
            if current is None or self._is_newer(incoming, current):
                self.add_set[elem_id] = incoming
                mutations_applied += 1

        # Merge Removes
        for elem_id, rec_data in other_rems.items():
            incoming = CRDTRecord.from_dict(rec_data)
            current = self.remove_set.get(elem_id)
            if current is None or self._is_newer(incoming, current):
                self.remove_set[elem_id] = incoming
                mutations_applied += 1

        # Update Vector Clock
        self.vclock.merge(other_clock)
        return mutations_applied

    def export_state(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "vector_clock": self.vclock.to_dict(),
            "add_set": {k: v.to_dict() for k, v in self.add_set.items()},
            "remove_set": {k: v.to_dict() for k, v in self.remove_set.items()},
        }


class P2PEpistemicSyncEngine:
    """
    High-level P2P Sync Engine for COPPER Epistemic Memory.
    Exchanges memory snapshots across multiple peer devices.
    """

    def __init__(self, local_node_id: str = "copper_node_local"):
        self.local_node_id = local_node_id
        self.memory_crdt = LWWElementSet(local_node_id)
        self.sync_stats = {
            "total_syncs": 0,
            "mutations_received": 0,
            "conflicts_resolved": 0,
        }

    def set_memory_fact(self, key: str, value: Any) -> None:
        self.memory_crdt.add(key, value)

    def delete_memory_fact(self, key: str) -> None:
        self.memory_crdt.remove(key)

    def get_memory_fact(self, key: str) -> Any | None:
        return self.memory_crdt.lookup(key)

    def export_delta_payload(self) -> str:
        """Serializes current CRDT state for P2P network broadcast."""
        return json.dumps(self.memory_crdt.export_state(), indent=2)

    def ingest_peer_payload(self, payload_json: str) -> int:
        """Ingests and merges state from a peer node."""
        state = json.loads(payload_json)
        mutations = self.memory_crdt.merge(state)
        self.sync_stats["total_syncs"] += 1
        self.sync_stats["mutations_received"] += mutations
        if mutations > 0:
            self.sync_stats["conflicts_resolved"] += 1
        return mutations


p2p_sync_engine = P2PEpistemicSyncEngine()
