# COPPER Framework — Documentation Hub

> **Root:** [Project README](../README.md)

This directory is the single source of truth for the COPPER Framework. Every document below cross-links to the others — when in doubt, start with the [PRD](PRD.md) for *what* and *why*, the [TRD](TRD.md) for *how*, and [Implementation Guide](IMPLEMENTATION.md) for *the actual code*.

---

## Core Specification

| Document | Status | Description |
|---|---|---|
| [PRD.md](PRD.md) | Stable | Product vision, goals, the 30-agent roster, user stories & acceptance criteria, hardware constraints |
| [TRD.md](TRD.md) | Stable | System architecture pattern, 6-model specialist architecture, technology stack, technical requirements (TR-01–TR-07) |
| [APP_FLOW.md](APP_FLOW.md) | Stable | Execution flows: primary hot-swap loop, interrupt flow, passive vision flow, Boss Mode, frontend dashboard flow |
| [UI_UX_BRIEF.md](UI_UX_BRIEF.md) | Stable | Design system (AeroNet-derived tokens), dashboard component specs, layout, motion, ambient effects |
| [BACKEND_SCHEMA.md](BACKEND_SCHEMA.md) | Stable | `state.json` active-state schema and full SQLite (`copper.db`) schema with indexes |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | Stable | Directory structure, core engine code listings, fine-tuning pipeline, deployment & setup, implementation phases, known limitations |

---

## Reference Material

| Folder | Description |
|---|---|
| [`architecture/`](architecture/README.md) | Layered system architecture, aligned with [TRD §6](TRD.md#6-system-architecture-overview) |
| [`api/`](api/README.md) | Local-only API surface: Ollama inference API + dashboard bridge API |
| [`diagrams/`](diagrams/README.md) | Diagram catalog — flowcharts, sequence diagrams, ER diagrams, export instructions |
| [`research/`](research/README.md) | Model selection rationale, architecture alternatives considered, open questions / backlog |
| [`setup/`](setup/README.md) | Step-by-step setup & deployment guide, troubleshooting |

---

## Reading Order

For someone new to the project, the recommended reading order is:

1. [Project README](../README.md) — what COPPER is, in two minutes
2. [PRD.md](PRD.md) — vision, goals, the 30 agents, hardware envelope
3. [architecture/README.md](architecture/README.md) — how the system is laid out
4. [TRD.md](TRD.md) — the sequential hot-swap pattern and the 6-model architecture
5. [APP_FLOW.md](APP_FLOW.md) — what actually happens on a single user prompt
6. [BACKEND_SCHEMA.md](BACKEND_SCHEMA.md) — the data that flows through that loop
7. [UI_UX_BRIEF.md](UI_UX_BRIEF.md) — how it's presented to the user
8. [IMPLEMENTATION.md](IMPLEMENTATION.md) — the code
9. [setup/README.md](setup/README.md) — run it yourself

---

## Documentation Conventions

- **Status tags** (`Stable`, `Draft`, `Deprecated`) appear at the top of each document's index entry. A `Deprecated` document remains in the repo for historical traceability but must not be treated as current guidance — see [research/architecture-alternatives.md](research/architecture-alternatives.md) for an example.
- **Cross-links** use relative paths and, where possible, point to a specific section anchor (e.g. `TRD.md#61-architecture-pattern-sequential-hot-swap-engine`) rather than just the document, so references don't go stale silently when sections are reordered.
- **Source of truth hierarchy:** if two documents disagree, [PRD.md](PRD.md) wins on *product* questions (goals, non-goals, agent roster) and [TRD.md](TRD.md) wins on *technical* questions (architecture pattern, stack, hardware enforcement). Any document that cannot be reconciled with these two must be flagged and moved to `research/` until resolved.
- **Open items** (ambiguities, unresolved duplicates, TODOs) are called out inline with a `> **Open item:**` blockquote rather than silently resolved, so they remain visible until explicitly closed. See [PRD §3, footnote 1](PRD.md#3-the-30-agents--full-roster) for the current open item (duplicate `NEXUS` entry).
