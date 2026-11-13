# Shared Architectural Contracts and Interfaces

All cross-foundation communication within C.O.P.P.E.R. adheres to strongly-typed contracts defined in [`backend/app/core/interfaces/contracts.py`](file:///d:/C.O.P.P.E.R/backend/app/core/interfaces/contracts.py).

---

## 1. ExecutionContext

`ExecutionContext` represents the unified runtime envelope carrying identity, policy, tracing, and constraints across asynchronous boundaries.

```python
@dataclass
class ExecutionContext:
    request_id: str                      # Globally unique request identifier (e.g., "req_a1b2c3d4")
    trace_id: str                        # W3C distributed trace identifier (e.g., "trc_1234567890abcdef")
    task_id: str                         # Specific task identifier (e.g., "tsk_fedcba987654")
    user_id: Optional[str]               # Authenticated actor / local operator identity
    session_id: Optional[str]            # Current interactive desktop / chat session
    agent_id: Optional[str]              # Active subagent codename (e.g., "AXIS", "FORGE")
    execution_origin: ExecutionOrigin    # API, DESKTOP, AGENT, SCHEDULE, INTERNAL, TOOL
    security_classification: str         # "standard", "privileged", "isolated"
    privacy_classification: DataSensitivity # PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED
    active_policy_version: str           # Version of governance policy pack ("1.0.0-sovereign")
    resource_budget: ResourceBudget      # Hardware constraints for this task
    deadline_seconds: Optional[float]    # Maximum execution deadline
    cancellation_token: CancellationToken# Cooperative cancellation token
    metadata: dict[str, Any]             # Key-value execution metadata
    created_at: float                    # Epoch timestamp of creation
```

---

## 2. PolicyDecision

`PolicyDecision` captures the authoritative verdict resulting from evaluating Security, Privacy, and Safety policies against a proposed action.

```python
@dataclass
class PolicyDecision:
    decision: PolicyVerdict              # ALLOW, DENY, REQUIRE_APPROVAL
    applicable_policy: str               # Canonical rule identifier (e.g., "SEC-001-LOCAL-FIRST")
    reason: str                          # Human-readable justification
    required_controls: list[str]         # Mandatory guardrails (e.g., ["audit_trail", "metering"])
    validity_scope: str                  # Scope of verdict validity ("request", "session")
    audit_reference: str                 # Correlated audit event token
    timestamp: float                     # Evaluation epoch timestamp
```

---

## 3. ResourceBudget

`ResourceBudget` specifies the compute, memory, storage, and networking limits allocated to an execution context, strictly enforcing hardware boundaries.

```python
@dataclass
class ResourceBudget:
    cpu_cores_max: float = 2.0
    ram_bytes_max: int = 4 * 1024 * 1024 * 1024         # 4.0 GB Host RAM
    vram_bytes_max: int = 8 * 1024 * 1024 * 1024        # <= 8.0 GB Physical VRAM ceiling
    max_execution_time_seconds: float = 60.0
    max_inference_tokens: int = 4096
    max_tool_steps: int = 5
    max_queue_wait_seconds: float = 15.0
    storage_allowance_bytes: int = 100 * 1024 * 1024    # 100 MB scratch storage
    network_egress_allowed: bool = False                 # Local-first zero external egress
    cancellation_conditions: list[str] = field(
        default_factory=lambda: ["timeout", "vram_exceeded", "user_abort"]
    )
```

---

## 4. AuditEvent

`AuditEvent` is an immutable, cryptographically chained record of execution events providing mathematical non-repudiation and tamper-evidence.

```python
@dataclass
class AuditEvent:
    event_id: str                        # Unique audit event identifier ("aud_...")
    timestamp: float                     # Timestamp of event occurrence
    actor: str                           # Executing identity (e.g., "AXIS", "local_operator")
    action: str                          # Action name (e.g., "tool_execute:file_write")
    target: str                          # Target resource or subsystem
    outcome: str                         # SUCCESS, DENIED, FAILED, BLOCKED, SHED
    reason: str                          # Outcome explanation or error message
    trace_id: str                        # Correlated W3C trace ID
    task_id: str                         # Correlated task ID
    policy_version: str                  # Active governance policy version
    integrity_hash: str                  # HMAC-SHA256 signature sealing this event
    previous_event_hash: str             # Integrity hash of previous block (Hash Chain)
    details: dict[str, Any]              # Structured parameters, redacted payloads, metrics
```

---

## 5. HealthStatus

`HealthStatus` exposes operational readiness, dependency status, and hardware resource saturation.

```python
@dataclass
class HealthStatus:
    component_id: str                    # Subsystem identifier
    operational_state: ComponentState    # HEALTHY, DEGRADED, FAILED, UNAVAILABLE
    readiness: bool                      # Readiness to accept new tasks
    dependency_health: dict[str, bool]   # Health of downstream dependencies
    degraded_mode_info: Optional[str]    # Remediation info if degraded
    last_successful_operation: Optional[float]
    vram_allocated_bytes: int            # Current physical VRAM allocation
    active_tasks: int                    # Currently running concurrent operations
```
