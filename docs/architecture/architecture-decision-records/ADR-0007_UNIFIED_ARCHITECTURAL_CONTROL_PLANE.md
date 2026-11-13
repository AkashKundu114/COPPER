# ADR-0007: Unified Architectural Control Plane & Standardized Execution Lifecycle

- **Status:** Accepted
- **Date:** 2026-11-10
- **Authors:** Principal Software Architect, Staff-level Systems Engineer, Security Architect
- **Applies to:** Core Architecture, Multi-Agent Runtime, Tool Execution, API Ingress

---

## Context
COPPER evolved through 13 progressive engineering stages addressing 12 foundational engineering domains (Zero-Trust Security, Unified Observability, Reliability & Resilience, Privacy & Data Governance, Safety & Alignment, Performance & Optimization, Scalability, Interoperability, Configuration & Policy, Auditability, Maintainability, Cost & Resource Governance).

While individual subsystem implementations were complete and verified in isolation, there was a risk of architectural divergence:
- Different subsystems used ad-hoc contexts, disparate error schemas, and varying authorization hooks.
- Tool executions and background tasks lacked unified resource budgeting and cryptographic audit trails.
- Cross-cutting concerns (PII redaction, indirect injection defense, VRAM limits) were invoked intermittently rather than systematically.

## Decision
1. **Unified Control Plane:** Establish a centralized, non-monolithic `ArchitecturalControlPlane` (`backend/app/core/control_plane.py`) that coordinates all 12 foundations.
2. **Shared Contracts:** Standardize all inter-subsystem data structures around five canonical contracts (`ExecutionContext`, `PolicyDecision`, `ResourceBudget`, `AuditEvent`, `HealthStatus`).
3. **Mandatory 15-Step Lifecycle:** Standardize every request execution into a deterministic 15-step lifecycle ensuring:
   - Zero-trust authorization and privacy classification before execution.
   - Resource budget admission checks enforcing $\le 8.0\text{ GB}$ VRAM.
   - Output validation and prompt injection neutralization.
   - Guaranteed resource release in `finally` blocks.
   - Cryptographic HMAC-SHA256 hash-chained audit logging.
4. **Strict Layer Boundary Isolation:** Enforce ADR-0005: Low-level modules (`app.core`, `app.database`) never import high-level modules (`app.ai`, `app.api`), verified by static AST analysis.

## Consequences
- **Positive:**
  - One unified execution context and policy model across API, UI, agents, tools, and background tasks.
  - Zero bypass paths for safety, security, and resource boundaries.
  - Cryptographically verifiable audit trail for all operations.
  - Consistent error formats and correlation IDs (`X-Trace-Id`) across the platform.
- **Trade-offs:**
  - Slight overhead (approx. 2–5ms) per execution lifecycle for cryptographic hashing and policy evaluation. This is acceptable given the local workstation environment and critical security requirements.
