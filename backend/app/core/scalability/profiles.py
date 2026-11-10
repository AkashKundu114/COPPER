"""Deployment Profile Manager for C.O.P.P.E.R.

Defines operational characteristics, resource limits, and coordination
mechanisms across three distinct deployment topologies:
  1. DESKTOP: Standalone personal workstation (zero external dependencies).
  2. HOMELAB: Single-server container stack (Docker Compose, PostgreSQL, Redis).
  3. CLUSTER: Multi-node cloud-native environment (Kubernetes, stateless replicas).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.core.logger import logger


class DeploymentProfile(str, Enum):
    DESKTOP = "desktop"
    HOMELAB = "homelab"
    CLUSTER = "cluster"


class SessionStorageBackend(str, Enum):
    LOCAL_JSON = "local_json"
    REDIS = "redis"
    POSTGRES = "postgres"


@dataclass(frozen=True)
class ProfileSpecification:
    profile: DeploymentProfile
    name: str
    description: str
    session_backend: SessionStorageBackend
    enable_distributed_locking: bool
    enable_multi_replica_sync: bool
    db_pool_size: int
    db_max_overflow: int
    redis_required: bool
    max_worker_concurrency: int
    enable_hpa: bool


PROFILE_SPECIFICATIONS: dict[DeploymentProfile, ProfileSpecification] = {
    DeploymentProfile.DESKTOP: ProfileSpecification(
        profile=DeploymentProfile.DESKTOP,
        name="Personal Desktop",
        description="Air-gapped, zero-external-dependency local workstation running SQLite WAL and in-memory caches.",
        session_backend=SessionStorageBackend.LOCAL_JSON,
        enable_distributed_locking=False,
        enable_multi_replica_sync=False,
        db_pool_size=5,
        db_max_overflow=0,
        redis_required=False,
        max_worker_concurrency=2,
        enable_hpa=False,
    ),
    DeploymentProfile.HOMELAB: ProfileSpecification(
        profile=DeploymentProfile.HOMELAB,
        name="Single-Server Homelab",
        description="Docker Compose multi-service architecture using PostgreSQL, Redis, and local GPU Ollama.",
        session_backend=SessionStorageBackend.REDIS,
        enable_distributed_locking=True,
        enable_multi_replica_sync=True,
        db_pool_size=20,
        db_max_overflow=10,
        redis_required=True,
        max_worker_concurrency=4,
        enable_hpa=False,
    ),
    DeploymentProfile.CLUSTER: ProfileSpecification(
        profile=DeploymentProfile.CLUSTER,
        name="Multi-Node Cluster",
        description="Kubernetes multi-pod deployment with stateless API replicas and distributed coordination.",
        session_backend=SessionStorageBackend.REDIS,
        enable_distributed_locking=True,
        enable_multi_replica_sync=True,
        db_pool_size=50,
        db_max_overflow=25,
        redis_required=True,
        max_worker_concurrency=8,
        enable_hpa=True,
    ),
}


class ProfileManager:
    """Detects and provides the active deployment profile specification."""

    def __init__(self):
        self._active_profile = self._detect_profile()

    def _detect_profile(self) -> DeploymentProfile:
        env_val = os.environ.get("COPPER_PROFILE", "").lower().strip()
        if env_val in (p.value for p in DeploymentProfile):
            return DeploymentProfile(env_val)

        # Kubernetes detection heuristic
        if os.environ.get("KUBERNETES_SERVICE_HOST"):
            return DeploymentProfile.CLUSTER

        # Docker Compose detection heuristic
        if os.path.exists("/.dockerenv") or os.environ.get("POSTGRES_HOST"):
            return DeploymentProfile.HOMELAB

        # Default to local desktop
        return DeploymentProfile.DESKTOP

    @property
    def active_profile(self) -> DeploymentProfile:
        return self._active_profile

    @property
    def current_spec(self) -> ProfileSpecification:
        return PROFILE_SPECIFICATIONS[self._active_profile]

    def set_profile(self, profile: DeploymentProfile) -> None:
        """Explicitly sets deployment profile (used in testing or reconfiguration)."""
        self._active_profile = profile
        logger.info(f"[ProfileManager] Active profile set to: {profile.value}")

    def to_dict(self) -> dict[str, Any]:
        spec = self.current_spec
        return {
            "active_profile": spec.profile.value,
            "name": spec.name,
            "description": spec.description,
            "session_backend": spec.session_backend.value,
            "enable_distributed_locking": spec.enable_distributed_locking,
            "enable_multi_replica_sync": spec.enable_multi_replica_sync,
            "db_pool_size": spec.db_pool_size,
            "db_max_overflow": spec.db_max_overflow,
            "redis_required": spec.redis_required,
            "max_worker_concurrency": spec.max_worker_concurrency,
        }


profile_manager = ProfileManager()
