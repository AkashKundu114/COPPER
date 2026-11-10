"""Consistent Hash Ring with Virtual Nodes (vnodes) Workload Router.

Implements Stage 10 Scalability Architecture:
- Maps partition keys to distributed worker nodes via a 32-bit/64-bit circular hash ring.
- Utilizes virtual nodes (vnodes) to guarantee uniform distribution and eliminate hotspotting.
- Minimizes key re-allocation churn during dynamic node scaling.
"""

from __future__ import annotations

import bisect
import hashlib
from dataclasses import dataclass, field
from typing import Optional


class ConsistentHashRingRouter:
    """Consistent hashing ring with virtual nodes for partition key routing."""

    def __init__(self, replicas_per_node: int = 100) -> None:
        self.replicas_per_node = replicas_per_node
        self._ring: dict[int, str] = {}  # hash_val -> physical_node_id
        self._sorted_keys: list[int] = []
        self._nodes: set[str] = set()

    def _hash(self, key_str: str) -> int:
        """Compute 32-bit integer hash from string."""
        return int(hashlib.md5(key_str.encode("utf-8")).hexdigest()[:8], 16)

    def add_node(self, node_id: str) -> None:
        """Add a physical node and its virtual replicas to the hash ring."""
        self._nodes.add(node_id)
        for i in range(self.replicas_per_node):
            vnode_key = f"{node_id}#vnode-{i}"
            h = self._hash(vnode_key)
            self._ring[h] = node_id
            bisect.insort(self._sorted_keys, h)

    def remove_node(self, node_id: str) -> None:
        """Remove a physical node and its virtual replicas from the hash ring."""
        if node_id not in self._nodes:
            return
        self._nodes.remove(node_id)
        for i in range(self.replicas_per_node):
            vnode_key = f"{node_id}#vnode-{i}"
            h = self._hash(vnode_key)
            self._ring.pop(h, None)
            idx = bisect.bisect_left(self._sorted_keys, h)
            if idx < len(self._sorted_keys) and self._sorted_keys[idx] == h:
                self._sorted_keys.pop(idx)

    def get_node(self, partition_key: str) -> Optional[str]:
        """Route a partition key to the nearest clockwise node on the ring."""
        if not self._ring:
            return None

        h = self._hash(partition_key)
        idx = bisect.bisect_right(self._sorted_keys, h)
        if idx == len(self._sorted_keys):
            idx = 0  # Wrap around ring

        target_hash = self._sorted_keys[idx]
        return self._ring[target_hash]

    def get_nodes_count(self) -> int:
        return len(self._nodes)
