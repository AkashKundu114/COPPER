"""Modular Domain-Specific Configuration Schemas for C.O.P.P.E.R.

Replaces flat monolithic settings with strongly typed, validated, and
reconciled domain models supporting hot-reload and change auditing.
"""

from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field


class AppIdentityConfig(BaseModel):
    app_name: str = Field(default="COPPER", description="Canonical application name")
    app_version: str = Field(default="3.0.0", description="SemVer release version (reconciled across docs/code)")
    app_env: str = Field(default="development", description="Runtime environment: development, production, test")
    demo_mode: bool = Field(default=False, description="Flag for presentation/demo mode")


class DatabaseConfig(BaseModel):
    database_url: str = Field(
        default="sqlite:///data/copper_memory.db",
        description="SQLAlchemy connection URI",
    )
    pool_size: int = Field(default=20, ge=1, le=100)
    max_overflow: int = Field(default=10, ge=0, le=50)
    pool_recycle_seconds: int = Field(default=300, ge=30)
    enable_wal_mode: bool = Field(default=True, description="Enables PRAGMA journal_mode=WAL on SQLite")


class ModelRuntimeConfig(BaseModel):
    ollama_base_url: str = Field(default="http://localhost:11434")
    vram_budget_gb: float = Field(default=8.0, ge=2.0, le=48.0, description="Host GPU VRAM budget")
    gatekeeper_model: str = Field(default="qwen2.5:1.5b", description="Pinned gatekeeper model name")
    gatekeeper_keep_alive: int = Field(default=-1, description="-1 keeps permanently loaded")
    heavy_model_idle_unload_seconds: int = Field(default=240, ge=10, le=3600)
    max_concurrent_inferences: int = Field(default=2, ge=1, le=16)


class SandboxConfig(BaseModel):
    backend: str = Field(default="auto", description="Isolation backend: auto, pyodide, docker")
    timeout_seconds: int = Field(default=15, ge=1, le=120)
    memory_limit_mb: int = Field(default=256, ge=64, le=4096)
    cpu_limit: float = Field(default=1.0, ge=0.1, le=8.0)
    network_enabled: bool = Field(default=False, description="Enforce strict network airgap for untrusted code")


class NetworkPolicyConfig(BaseModel):
    network_mode: str = Field(
        default="user_authorized_egress",
        description="offline_airgap, local_services, or user_authorized_egress",
    )
    ssrf_protection_enabled: bool = Field(default=True)
    rate_limit_enabled: bool = Field(default=True)
    searxng_url: str = Field(default="http://localhost:8888")


class SecurityConfig(BaseModel):
    auth_enforced: bool = Field(default=False, description="Enforce JWT/Bearer auth on API routes")
    token_expiry_minutes: int = Field(default=60, ge=5, le=10080)
    secret_vault_enabled: bool = Field(default=True)
    pii_redaction_enabled: bool = Field(default=True)


class ObservabilityConfig(BaseModel):
    otel_enabled: bool = Field(default=False)
    otel_service_name: str = Field(default="copper-backend")
    otlp_endpoint: str = Field(default="http://localhost:4317")
    prometheus_metrics_enabled: bool = Field(default=True)


class COPPERConfig(BaseModel):
    """Unified master configuration container aggregating all domain schemas."""
    identity: AppIdentityConfig = Field(default_factory=AppIdentityConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    model_runtime: ModelRuntimeConfig = Field(default_factory=ModelRuntimeConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    network: NetworkPolicyConfig = Field(default_factory=NetworkPolicyConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    observability: ObservabilityConfig = Field(default_factory=ObservabilityConfig)


master_config = COPPERConfig()
