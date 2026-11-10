# ADR-0005: Layered Architecture Boundaries & Dependency Invariants

## Status
**Accepted**

## Context
As COPPER expands, unconstrained imports between high-level agents, low-level database utilities, and API route handlers introduce circular dependencies, tight coupling, and brittle test suites.

## Decision
Establish a strict 4-tier unidirectional dependency hierarchy:
1. **Layer 1: Presentation & Ingress (`app.api`)**
2. **Layer 2: AI & Orchestration (`app.ai`)**
3. **Layer 3: Domain Core & Security (`app.core`)**
4. **Layer 4: Data & Persistence Infrastructure (`app.database`)**

### Dependency Invariant Rule:
Dependencies must only flow downward: $\text{Layer } N \to \text{Layer } (N+1)$.
- `app.database` and `app.core` must never import from `app.ai` or `app.api`.
- An automated AST-based import linter (`scripts/lint_architecture.py`) enforces this rule in CI.

## Consequences
- **Positive**: High modularity, zero circular import bugs, clean unit test isolation, and clear component ownership.
- **Negative**: Requires shared models or interfaces to reside in Core or Database rather than in high-level agent modules.
