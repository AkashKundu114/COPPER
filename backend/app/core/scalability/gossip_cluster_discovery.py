"""Decentralized Epidemic Gossip Protocol and Peer Node Discovery.

Implements Stage 8 Scalability Architecture:
- Discovers peer nodes via randomized epidemic gossip message dissemination.
- Tracks node state: ALIVE, SUSPECT, DEAD with configurable failure detection timeouts.
- Disseminates cluster membership, load status, and health metrics without a central coordinator.
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class NodeStatus(str, Enum):
    ALIVE = "ALIVE"
    SUSPECT = "SUSPECT"
    DEAD = "DEAD"


@dataclass
class PeerNodeDescriptor:
    node_id: str
    host: str
    port: int
    status: NodeStatus
    incarnation: int
    last_heartbeat: float
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class GossipDigest:
    sender_id: str
    incarnation: int
    membership_view: list[PeerNodeDescriptor]
    timestamp: float = field(default_factory=time.time)


class GossipClusterDiscovery:
    """Decentralized gossip-based membership and peer discovery protocol."""

    def __init__(
        self,
        local_node_id: str,
        host: str = "127.0.0.1",
        port: int = 8000,
        suspect_timeout_seconds: float = 10.0,
        dead_timeout_seconds: float = 30.0,
    ) -> None:
        self.local_node_id = local_node_id
        self.host = host
        self.port = port
        self.suspect_timeout_seconds = suspect_timeout_seconds
        self.dead_timeout_seconds = dead_timeout_seconds
        self.incarnation = 1

        self._members: dict[str, PeerNodeDescriptor] = {
            local_node_id: PeerNodeDescriptor(
                node_id=local_node_id,
                host=host,
                port=port,
                status=NodeStatus.ALIVE,
                incarnation=self.incarnation,
                last_heartbeat=time.time(),
                metadata={"role": "worker"},
            )
        }

    def register_peer(self, node_id: str, host: str, port: int, metadata: Optional[dict[str, str]] = None) -> None:
        """Register or update a peer node in the local membership view."""
        self._members[node_id] = PeerNodeDescriptor(
            node_id=node_id,
            host=host,
            port=port,
            status=NodeStatus.ALIVE,
            incarnation=1,
            last_heartbeat=time.time(),
            metadata=metadata or {},
        )

    def prepare_gossip_digest(self) -> GossipDigest:
        """Create a membership digest to send to a randomly selected peer."""
        # Update self heartbeat
        local = self._members[self.local_node_id]
        local.last_heartbeat = time.time()
        local.incarnation = self.incarnation

        return GossipDigest(
            sender_id=self.local_node_id,
            incarnation=self.incarnation,
            membership_view=list(self._members.values()),
        )

    def process_incoming_gossip(self, digest: GossipDigest) -> int:
        """Merge a peer's gossip digest into local membership view. Returns count of updated nodes."""
        updates = 0
        now = time.time()

        for peer in digest.membership_view:
            if peer.node_id == self.local_node_id:
                # If peer thinks we are SUSPECT/DEAD, increment incarnation to refute
                if peer.status != NodeStatus.ALIVE and peer.incarnation >= self.incarnation:
                    self.incarnation = peer.incarnation + 1
                    self._members[self.local_node_id].incarnation = self.incarnation
                    self._members[self.local_node_id].status = NodeStatus.ALIVE
                    updates += 1
                continue

            current = self._members.get(peer.node_id)
            if current is None:
                self._members[peer.node_id] = peer
                updates += 1
            else:
                if peer.incarnation > current.incarnation:
                    self._members[peer.node_id] = peer
                    updates += 1
                elif peer.incarnation == current.incarnation:
                    if peer.status == NodeStatus.DEAD and current.status != NodeStatus.DEAD:
                        current.status = NodeStatus.DEAD
                        updates += 1
                    elif peer.status == NodeStatus.SUSPECT and current.status == NodeStatus.ALIVE:
                        current.status = NodeStatus.SUSPECT
                        updates += 1
                    elif peer.last_heartbeat > current.last_heartbeat:
                        current.last_heartbeat = peer.last_heartbeat
                        if current.status == NodeStatus.SUSPECT:
                            current.status = NodeStatus.ALIVE
                        updates += 1

        return updates

    def evaluate_node_health(self) -> dict[NodeStatus, list[str]]:
        """Evaluate timeouts and transition stale nodes from ALIVE -> SUSPECT -> DEAD."""
        now = time.time()
        results: dict[NodeStatus, list[str]] = {
            NodeStatus.ALIVE: [],
            NodeStatus.SUSPECT: [],
            NodeStatus.DEAD: [],
        }

        for node_id, desc in self._members.items():
            if node_id == self.local_node_id:
                results[NodeStatus.ALIVE].append(node_id)
                continue

            elapsed = now - desc.last_heartbeat
            if desc.status == NodeStatus.ALIVE and elapsed > self.suspect_timeout_seconds:
                desc.status = NodeStatus.SUSPECT
            elif desc.status == NodeStatus.SUSPECT and elapsed > self.dead_timeout_seconds:
                desc.status = NodeStatus.DEAD

            results[desc.status].append(node_id)

        return results

    def get_alive_nodes(self) -> list[PeerNodeDescriptor]:
        return [n for n in self._members.values() if n.status == NodeStatus.ALIVE]

    def select_random_gossip_targets(self, fanout: int = 3) -> list[PeerNodeDescriptor]:
        """Select a random subset of alive peers to gossip with."""
        candidates = [n for n in self._members.values() if n.node_id != self.local_node_id and n.status != NodeStatus.DEAD]
        count = min(fanout, len(candidates))
        return random.sample(candidates, count) if count > 0 else []
