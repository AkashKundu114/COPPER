# Contributing to C.O.P.P.E.R.: Architectural Standards & Guidelines

Welcome! To ensure C.O.P.P.E.R. remains modular, secure, and performant under the strict **8GB VRAM constraint** and **local-first philosophy**, all contributions must comply with the following architectural standards.

---

## 1. Core Principles

1. **Local-First Operating Guarantee**: All primary reasoning and storage must function offline without mandatory cloud dependencies.
2. **8GB VRAM Operating Invariant**: No model or agent change may violate the 8.0 GB VRAM limit. All models must be hot-swapped via `VRAMPager` or verified via `QuantizationVRAMEstimator`.
3. **Layered Boundary Invariant**: Review [ADR-0005](file:///d:/C.O.P.P.E.R/docs/adr/ADR-0005_LAYERED_ARCHITECTURE_BOUNDARIES.md). `app.core` and `app.database` must never import from `app.ai` or `app.api`.
4. **Zero-Trust Tool Gating**: All new tools must declare JSON schemas, declare a `guardian_level`, and be registered with `ToolAuthorizationPolicy`.

---

## 2. Pre-Commit Quality Gates

Before submitting a Pull Request, run the local verification suite:

```powershell
# 1. Architectural Boundary Linter
python scripts/lint_architecture.py

# 2. Ruff Linting & Formatting
ruff check .

# 3. Consolidated Test Suite
python -m pytest tests/architecture/ tests/privacy/ tests/security/ tests/reliability/ tests/observability/ -q
```

---

## 3. Adding New Features

- **Adding a New Agent**: Define your agent in `backend/app/ai/agents/`, inherit from `BaseAgent`, declare supported capabilities in `AgentCapability`, and register with `CORE_ACTIVE_AGENTS`.
- **Adding a New Tool**: Use the `@tool_registry.tool` decorator in `backend/app/ai/tools/builtin/`, define parameter types, and assign an appropriate `guardian_level` (0 for read-only, 1 for safe mutation, 2 for consequential disk/network write).
- **Adding a New Configuration Property**: Add the typed field to the appropriate domain model in `backend/app/core/configuration/schemas.py`. Never add flat unvalidated keys to global settings.
