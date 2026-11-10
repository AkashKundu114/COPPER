# ADR-0006: Extensible Model Runtime & Storage Provider Adapters

## Status
**Accepted**

## Context
Directly hardcoding Ollama HTTP endpoints and SQLite/PostgreSQL connection calls throughout high-level business logic couples COPPER to specific local tooling, making mock-testing and multi-node provider hot-swapping complex.

## Decision
1. **Abstract Protocols**: Define formal Python typing protocols (`ModelRuntimeProtocol`, `StorageAdapterProtocol`, `SearchProviderProtocol`) in `backend/app/core/interfaces/runtime_protocols.py`.
2. **Pluggable Implementations**: Concrete adapters implement these protocols without altering agent orchestration code.
3. **Runtime Substitution**: Allows seamless switching between Ollama, vLLM, mock test runners, local SQLite, and distributed PostgreSQL.

## Consequences
- **Positive**: High testability, decoupled dependencies, and vendor independence.
- **Negative**: Requires interface adherence and wrapper adapters for concrete libraries.
