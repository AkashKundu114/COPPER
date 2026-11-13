"""Unified Architectural Contracts and Interfaces for C.O.P.P.E.R.

Establishes the authoritative shared contracts for cross-foundation communication:
- ExecutionContext
- PolicyDecision
- ResourceBudget
- AuditEvent
- HealthStatus
- ExecutionResult

All subsystems across API, Core, AI, Agents, Tools, and Memory inherit and implement
these contracts to ensure deterministic governance, observability, resilience, and safety.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class PolicyVerdict(str, Enum):
    """Authoritative policy decision verdicts."""
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"


class DataSensitivity(str, Enum):
    """Privacy and sensitivity classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ComponentState(str, Enum):
    """Component operational health states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"


class ExecutionOrigin(str, Enum):
    """Origin source of an execution request."""
    API = "api"
    DESKTOP = "desktop"
    AGENT = "agent"
    SCHEDULE = "schedule"
    INTERNAL = "internal"
    TOOL = "tool"


class CancellationToken:
    """Async-safe cancellation token propagating cancellation across DAG dependencies."""

    def __init__(self):
        self._is_cancelled = False
        self._cancel_reason: Optional[str] = None
        self._callbacks: list[Any] = []

    @property
    def is_cancelled(self) -> bool:
        return self._is_cancelled

    @property
    def cancel_reason(self) -> Optional[str]:
        return self._cancel_reason

    def cancel(self, reason: str = "Execution cancelled by caller.") -> None:
        """Trigger cancellation and invoke registered callbacks."""
        if not self._is_cancelled:
            self._is_cancelled = True
            self._cancel_reason = reason
            for cb in self._callbacks:
                try:
                    if asyncio.iscoroutinefunction(cb):
                        asyncio.create_task(cb(reason))
                    else:
                        cb(reason)
                except Exception:
                    pass

    def add_callback(self, callback: Any) -> None:
        """Register a cancellation handler."""
        if self._is_cancelled:
            try:
                callback(self._cancel_reason or "Cancelled")
            except Exception:
                pass
        else:
            self._callbacks.append(callback)


@dataclass
class ResourceBudget:
    """Resource constraints allocated for a single execution lifecycle.
    
    Guarantees execution remains within local hardware bounds, specifically
    enforcing the physical 8.0 GB VRAM ceiling.
    """
    cpu_cores_max: float = 2.0
    ram_bytes_max: int = 4 * 1024 * 1024 * 1024  # 4.0 GB
    vram_bytes_max: int = 8 * 1024 * 1024 * 1024  # Strict <= 8.0 GB Physical VRAM ceiling
    max_execution_time_seconds: float = 60.0
    max_inference_tokens: int = 4096
    max_tool_steps: int = 5
    max_queue_wait_seconds: float = 15.0
    storage_allowance_bytes: int = 100 * 1024 * 1024  # 100 MB
    network_egress_allowed: bool = False  # Local-first zero external network egress
    cancellation_conditions: list[str] = field(default_factory=lambda: ["timeout", "vram_exceeded", "user_abort"])

    def validate_vram_invariant(self) -> bool:
        """Enforces that requested VRAM never exceeds the 8.0 GB hardware ceiling."""
        hard_limit = 8 * 1024 * 1024 * 1024
        return self.vram_bytes_max <= hard_limit

    def to_dict(self) -> dict[str, Any]:
        return {
            "cpu_cores_max": self.cpu_cores_max,
            "ram_bytes_max": self.ram_bytes_max,
            "vram_bytes_max": self.vram_bytes_max,
            "max_execution_time_seconds": self.max_execution_time_seconds,
            "max_inference_tokens": self.max_inference_tokens,
            "max_tool_steps": self.max_tool_steps,
            "max_queue_wait_seconds": self.max_queue_wait_seconds,
            "storage_allowance_bytes": self.storage_allowance_bytes,
            "network_egress_allowed": self.network_egress_allowed,
            "cancellation_conditions": self.cancellation_conditions,
        }


@dataclass
class PolicyDecision:
    """Result of policy evaluation across Security, Privacy, and Safety domains."""
    decision: PolicyVerdict
    applicable_policy: str
    reason: str
    required_controls: list[str] = field(default_factory=list)
    validity_scope: str = "request"
    audit_reference: str = field(default_factory=lambda: f"pol_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)

    @property
    def is_allowed(self) -> bool:
        return self.decision == PolicyVerdict.ALLOW

    @property
    def requires_approval(self) -> bool:
        return self.decision == PolicyVerdict.REQUIRE_APPROVAL

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision": self.decision.value,
            "applicable_policy": self.applicable_policy,
            "reason": self.reason,
            "required_controls": self.required_controls,
            "validity_scope": self.validity_scope,
            "audit_reference": self.audit_reference,
            "timestamp": self.timestamp,
        }


@dataclass
class ExecutionContext:
    """Unified execution context propagating across API, Agents, Models, Tools, and Storage."""
    request_id: str = field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")
    trace_id: str = field(default_factory=lambda: f"trc_{uuid.uuid4().hex[:16]}")
    task_id: str = field(default_factory=lambda: f"tsk_{uuid.uuid4().hex[:12]}")
    user_id: Optional[str] = "local_operator"
    session_id: Optional[str] = None
    agent_id: Optional[str] = None
    execution_origin: ExecutionOrigin = ExecutionOrigin.INTERNAL
    security_classification: str = "standard"
    privacy_classification: DataSensitivity = DataSensitivity.INTERNAL
    active_policy_version: str = "1.0.0-sovereign"
    resource_budget: ResourceBudget = field(default_factory=ResourceBudget)
    deadline_seconds: Optional[float] = None
    cancellation_token: CancellationToken = field(default_factory=CancellationToken)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)

    def is_expired(self) -> bool:
        if self.deadline_seconds is not None:
            return (time.time() - self.created_at) > self.deadline_seconds
        return False

    def create_child(self, agent_id: Optional[str] = None, task_id: Optional[str] = None) -> ExecutionContext:
        """Creates a correlated child execution context for sub-tasks or agents."""
        return ExecutionContext(
            request_id=self.request_id,
            trace_id=self.trace_id,
            task_id=task_id or f"tsk_{uuid.uuid4().hex[:12]}",
            user_id=self.user_id,
            session_id=self.session_id,
            agent_id=agent_id or self.agent_id,
            execution_origin=self.execution_origin,
            security_classification=self.security_classification,
            privacy_classification=self.privacy_classification,
            active_policy_version=self.active_policy_version,
            resource_budget=self.resource_budget,
            deadline_seconds=self.deadline_seconds,
            cancellation_token=self.cancellation_token,
            metadata=dict(self.metadata),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "execution_origin": self.execution_origin.value,
            "security_classification": self.security_classification,
            "privacy_classification": self.privacy_classification.value,
            "active_policy_version": self.active_policy_version,
            "resource_budget": self.resource_budget.to_dict(),
            "deadline_seconds": self.deadline_seconds,
            "metadata": self.metadata,
            "created_at": self.created_at,
        }


@dataclass
class AuditEvent:
    """Tamper-evident audit record with cryptographic hash-chaining."""
    event_id: str = field(default_factory=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    timestamp: float = field(default_factory=time.time)
    actor: str = "system"
    action: str = "execute"
    target: str = "unknown"
    outcome: str = "SUCCESS"  # SUCCESS, DENIED, FAILED, BLOCKED
    reason: str = ""
    trace_id: str = ""
    task_id: str = ""
    policy_version: str = "1.0.0-sovereign"
    integrity_hash: str = ""
    previous_event_hash: str = "0" * 64
    details: dict[str, Any] = field(default_factory=dict)

    def calculate_integrity_hash(self, secret_key: str = "copper_local_tamper_key") -> str:
        """Calculates HMAC-SHA256 integrity seal over immutable audit fields."""
        payload = (
            f"{self.event_id}:{self.timestamp}:{self.actor}:{self.action}:"
            f"{self.target}:{self.outcome}:{self.trace_id}:{self.task_id}:"
            f"{self.policy_version}:{self.previous_event_hash}"
        )
        return hmac.new(secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()

    def seal(self, previous_hash: str = "0" * 64, secret_key: str = "copper_local_tamper_key") -> AuditEvent:
        """Binds previous event hash and seals record with cryptographic integrity proof."""
        self.previous_event_hash = previous_hash
        self.integrity_hash = self.calculate_integrity_hash(secret_key)
        return self

    def verify_integrity(self, secret_key: str = "copper_local_tamper_key") -> bool:
        """Verifies that audit event has not been tampered with."""
        expected = self.calculate_integrity_hash(secret_key)
        return hmac.compare_digest(self.integrity_hash, expected)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "outcome": self.outcome,
            "reason": self.reason,
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "policy_version": self.policy_version,
            "integrity_hash": self.integrity_hash,
            "previous_event_hash": self.previous_event_hash,
            "details": self.details,
        }


@dataclass
class HealthStatus:
    """Operational health telemetry for a COPPER component."""
    component_id: str
    operational_state: ComponentState
    readiness: bool
    dependency_health: dict[str, bool] = field(default_factory=dict)
    degraded_mode_info: Optional[str] = None
    last_successful_operation: Optional[float] = None
    vram_allocated_bytes: int = 0
    active_tasks: int = 0

    @property
    def is_operational(self) -> bool:
        return self.operational_state in (ComponentState.HEALTHY, ComponentState.DEGRADED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "component_id": self.component_id,
            "operational_state": self.operational_state.value,
            "readiness": self.readiness,
            "dependency_health": self.dependency_health,
            "degraded_mode_info": self.degraded_mode_info,
            "last_successful_operation": self.last_successful_operation,
            "vram_allocated_bytes": self.vram_allocated_bytes,
            "active_tasks": self.active_tasks,
        }


@dataclass
class ExecutionResult:
    """Standardized response schema returned by the architectural control plane."""
    status: str  # "success", "error", "denied", "cancelled"
    data: Any
    context: Optional[dict[str, Any]] = None
    policy_decision: Optional[dict[str, Any]] = None
    execution_time_ms: float = 0.0
    trace_id: str = ""
    task_id: str = ""
    error: Optional[str] = None
    audit_event_id: Optional[str] = None

    @property
    def is_success(self) -> bool:
        return self.status == "success"

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "data": self.data,
            "context": self.context,
            "policy_decision": self.policy_decision,
            "execution_time_ms": self.execution_time_ms,
            "trace_id": self.trace_id,
            "task_id": self.task_id,
            "error": self.error,
            "audit_event_id": self.audit_event_id,
        }
