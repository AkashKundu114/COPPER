"""Cluster & Multi-Replica Coordination Architecture for C.O.P.P.E.R.

Manages replica heartbeats, distributed leader election, partition-safe task routing,
and seamless operation across Desktop, Homelab, and Multi-Node Cluster profiles.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from app.core.logger import logger
from app.core.scalability.distributed_lock import DistributedLockManager, distributed_lock_manager
from app.core.scalability.profiles import DeploymentProfile, profile_manager
from app.core.scalability.session_store import SharedSessionStore, shared_session_store


@dataclass
class NodeMetadata:
    node_id: str
    profile: DeploymentProfile
    hostname: str
    ip_address: str
    last_heartbeat: float = field(default_factory=time.time)
    is_leader: bool = False
    active_tasks_count: int = 0
    vram_free_gb: float = 8.0


class ClusterCoordinator:
    """Coordinates replica health, leader election, and distributed load dispatching."""

    def __init__(
        self,
        lock_manager: DistributedLockManager = distributed_lock_manager,
        sessions: SharedSessionStore = shared_session_store,
        node_id: str | None = None,
    ):
        self.lock_manager = lock_manager
        self.sessions = sessions
        self.node_id = node_id or f"node_{uuid.uuid4().hex[:8]}"
        self.profile = profile_manager.active_profile
        self._nodes: dict[str, NodeMetadata] = {}
        self.leader_id: str | None = None
        self._register_self()

    def _register_self(self) -> None:
        self_meta = NodeMetadata(
            node_id=self.node_id,
            profile=self.profile,
            hostname="localhost",
            ip_address="127.0.0.1",
            last_heartbeat=time.time(),
            is_leader=(self.profile == DeploymentProfile.DESKTOP),
        )
        self._nodes[self.node_id] = self_meta
        if self_meta.is_leader:
            self.leader_id = self.node_id
        logger.info(
            f"[ClusterCoordinator] Initialized node '{self.node_id}' under profile '{self.profile.value}'"
        )

    async def send_heartbeat(self, active_tasks: int = 0, vram_free_gb: float = 8.0) -> None:
        """Sends periodic node heartbeat and refreshes status in cluster registry."""
        if self.node_id in self._nodes:
            node = self._nodes[self.node_id]
            node.last_heartbeat = time.time()
            node.active_tasks_count = active_tasks
            node.vram_free_gb = vram_free_gb

    async def attempt_leader_election(self, ttl_sec: float = 15.0) -> bool:
        """Attempts to acquire the distributed leader role."""
        if self.profile == DeploymentProfile.DESKTOP:
            self.leader_id = self.node_id
            return True

        lock = await self.lock_manager.acquire_lock(
            resource="cluster:leader",
            lease_seconds=int(ttl_sec),
            timeout_seconds=0.2,
        )
        if lock:
            self.leader_id = self.node_id
            if self.node_id in self._nodes:
                self._nodes[self.node_id].is_leader = True
            logger.info(f"[ClusterCoordinator] Node '{self.node_id}' elected as cluster leader")
            return True
        return False

    def get_cluster_status(self) -> dict[str, Any]:
        """Returns the cluster topology and health metrics."""
        now = time.time()
        # Clean stale nodes (heartbeat > 60s)
        active_nodes = {
            nid: meta
            for nid, meta in self._nodes.items()
            if (now - meta.last_heartbeat) < 60.0
        }
        self._nodes = active_nodes

        return {
            "current_node_id": self.node_id,
            "profile": self.profile.value,
            "leader_id": self.leader_id,
            "active_node_count": len(self._nodes),
            "nodes": [
                {
                    "node_id": m.node_id,
                    "is_leader": m.is_leader,
                    "last_seen_sec_ago": round(now - m.last_heartbeat, 1),
                    "active_tasks": m.active_tasks_count,
                    "vram_free_gb": m.vram_free_gb,
                }
                for m in self._nodes.values()
            ],
        }


cluster_coordinator = ClusterCoordinator()
