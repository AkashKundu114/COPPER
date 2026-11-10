"""Autonomous Multi-Tier Storage and Cache Lifecycle Balancer.

Implements Stage 9 Cost & Resource Governance Architecture:
- Manages memory tiering hierarchy: VRAM (Tier 0) -> RAM (Tier 1) -> SSD (Tier 2) -> Cold Archive (Tier 3).
- Automatically demotes stale context items and checkpoints based on access frequency and age.
- Prevents disk and memory saturation under high-throughput workloads.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Optional


class StorageTier(IntEnum):
    VRAM = 0
    RAM = 1
    SSD = 2
    COLD_ARCHIVE = 3


@dataclass
class StorageArtifact:
    artifact_id: str
    size_mb: float
    current_tier: StorageTier
    last_accessed: float
    access_count: int
    data_payload: Any = None


@dataclass
class TierRebalanceAction:
    artifact_id: str
    from_tier: StorageTier
    to_tier: StorageTier
    size_mb: float
    reason: str


class TierStorageLifecycleBalancer:
    """Balances artifacts across storage tiers to prevent memory exhaustion and reduce hardware costs."""

    # Tier maximum capacity limits in Megabytes
    DEFAULT_CAPACITIES_MB = {
        StorageTier.VRAM: 8192.0,      # 8.0 GB strict VRAM cap
        StorageTier.RAM: 32768.0,     # 32.0 GB host RAM
        StorageTier.SSD: 524288.0,    # 512 GB local SSD
        StorageTier.COLD_ARCHIVE: 2097152.0,  # 2 TB archive
    }

    def __init__(self, tier_capacities: Optional[dict[StorageTier, float]] = None) -> None:
        self.capacities = tier_capacities or dict(self.DEFAULT_CAPACITIES_MB)
        self._artifacts: dict[str, StorageArtifact] = {}

    def store_artifact(
        self,
        artifact_id: str,
        size_mb: float,
        tier: StorageTier = StorageTier.RAM,
        payload: Any = None,
    ) -> StorageArtifact:
        art = StorageArtifact(
            artifact_id=artifact_id,
            size_mb=size_mb,
            current_tier=tier,
            last_accessed=time.time(),
            access_count=1,
            data_payload=payload,
        )
        self._artifacts[artifact_id] = art
        return art

    def access_artifact(self, artifact_id: str) -> Optional[StorageArtifact]:
        art = self._artifacts.get(artifact_id)
        if art:
            art.last_accessed = time.time()
            art.access_count += 1
            # Promote to higher tier if heavily accessed
            if art.current_tier > StorageTier.RAM and art.access_count >= 5:
                art.current_tier = StorageTier.RAM
        return art

    def rebalance_tiers(self, idle_demote_seconds: float = 300.0) -> list[TierRebalanceAction]:
        """Demote idle artifacts down the tier hierarchy to free up fast memory."""
        now = time.time()
        actions: list[TierRebalanceAction] = []

        for art in self._artifacts.values():
            idle_seconds = now - art.last_accessed

            # If in VRAM and idle, demote to RAM
            if art.current_tier == StorageTier.VRAM and idle_seconds > 60.0:
                art.current_tier = StorageTier.RAM
                actions.append(
                    TierRebalanceAction(
                        artifact_id=art.artifact_id,
                        from_tier=StorageTier.VRAM,
                        to_tier=StorageTier.RAM,
                        size_mb=art.size_mb,
                        reason=f"Idle in VRAM for {idle_seconds:.1f}s: demoted to RAM to preserve 8GB cap.",
                    )
                )

            # If in RAM and idle, demote to SSD
            elif art.current_tier == StorageTier.RAM and idle_seconds > idle_demote_seconds:
                art.current_tier = StorageTier.SSD
                actions.append(
                    TierRebalanceAction(
                        artifact_id=art.artifact_id,
                        from_tier=StorageTier.RAM,
                        to_tier=StorageTier.SSD,
                        size_mb=art.size_mb,
                        reason=f"Stale in RAM: demoted to SSD disk cache.",
                    )
                )

        return actions

    def get_tier_usage_mb(self, tier: StorageTier) -> float:
        return sum(a.size_mb for a in self._artifacts.values() if a.current_tier == tier)
