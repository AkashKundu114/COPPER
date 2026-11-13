"""Core interfaces and contracts for C.O.P.P.E.R."""

from app.core.interfaces.contracts import (
    AuditEvent,
    CancellationToken,
    ComponentState,
    DataSensitivity,
    ExecutionContext,
    ExecutionOrigin,
    ExecutionResult,
    HealthStatus,
    PolicyDecision,
    PolicyVerdict,
    ResourceBudget,
)
from app.core.interfaces.runtime_protocols import (
    ModelRuntimeProtocol,
    SearchProviderProtocol,
    StorageAdapterProtocol,
)

__all__ = [
    "AuditEvent",
    "CancellationToken",
    "ComponentState",
    "DataSensitivity",
    "ExecutionContext",
    "ExecutionOrigin",
    "ExecutionResult",
    "HealthStatus",
    "ModelRuntimeProtocol",
    "PolicyDecision",
    "PolicyVerdict",
    "ResourceBudget",
    "SearchProviderProtocol",
    "StorageAdapterProtocol",
]
