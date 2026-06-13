# Open Questions / Documentation Backlog

> **Documentation hub:** [docs/README.md](../README.md) · **Research index:** [research/README.md](README.md)
>
> **Status:** Living document — update in place as items are resolved. Each item should link to the document(s) it affects and, once resolved, to the document where the resolution now lives.

This is the single tracked list of open ambiguities, unresolved duplications, and unverified assumptions across the COPPER documentation set. Items are grouped by the document they primarily affect.

---

## PRD

### OQ-1: Duplicate `NEXUS` agent in the 30-agent roster

- **Location:** [PRD §3, footnote 1](../PRD.md#3-the-30-agents--full-roster)
- **Issue:** `NEXUS` appears twice — #6 "Git Manager" and #30 "Git Operations" — both under Model 2. Since `agent_profiles.agent_id` is a primary key ([Backend Schema §12.4](../BACKEND_SCHEMA.md#124-agent-profiles-table)), seeding the table with both rows under `agent_id = 'NEXUS'` will fail or silently overwrite.
- **Options:**
  1. Merge into a single `NEXUS` agent with combined responsibilities (version control + git operations) — yields a 29-agent roster, with slot #30 open for a new agent.
  2. Rename #30 to a distinct `agent_id` (e.g. `VAULT` or similar) with a clearly differentiated responsibility, preserving the 30-agent target.
- **Affects:** [PRD §3](../PRD.md#3-the-30-agents--full-roster), [Backend Schema §12.4](../BACKEND_SCHEMA.md#124-agent-profiles-table), [PRD Appendix B](../PRD.md#appendix-b-peer-rivalry-matrix) (NEXUS rivalry entries would need to specify which NEXUS)
- **Status:** Open

---

## TRD

### OQ-2: LoRA hot-swap latency target unverified

- **Location:** [TRD §7.5 TR-05](../TRD.md#75-tr-05-lora-adapter-hot-swap)
- **Issue:** The <100ms adapter injection target is specified but not yet benchmarked against `llama.cpp`'s `lora-scale` parameter on the target hardware (6 GB VRAM class GPU).
- **Affects:** [TRD §7.5](../TRD.md#75-tr-05-lora-adapter-hot-swap), [Implementation Guide §18](../IMPLEMENTATION.md#18-known-limitations--mitigations)
- **Status:** Open — needs a benchmark script and a results writeup in `research/`.

### OQ-3: Florence-2 / Ollama integration path

- **Location:** [TRD §6.2, Model 4](../TRD.md#62-the-6-model-specialist-architecture)
- **Issue:** Florence-2 (the lower-VRAM option for Model 4) is not natively served by Ollama. See [research/model-selection.md](model-selection.md#open-question-florence-2--ollama-integration) for the detailed tradeoff.
- **Affects:** [TRD §6.2](../TRD.md#62-the-6-model-specialist-architecture), [TRD §7.3](../TRD.md#73-tr-03-sequential-execution), [Implementation Guide §18](../IMPLEMENTATION.md#18-known-limitations--mitigations)
- **Status:** Open — proposed mitigation documented, not yet implemented/verified.

---

## App Flow

### OQ-4: `state.json` JSON-parsing logic in the main loop is a stub

- **Location:** [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop), comment `# (JSON parsing logic omitted for brevity)`
- **Issue:** The reference `run()` loop does not show how an agent's raw model output (a string) is parsed back into structured updates to `state.json` (e.g. updating `next_agent`, `task_context`, `dialogue_transcript`). This is a critical implementation detail — likely requires a strict output format contract per agent (e.g. requiring `[DIALOGUE]` / `[TECHNICAL_PAYLOAD]` blocks per [App Flow §8.5](../APP_FLOW.md#85-boss-mode-flow) to be machine-parseable even outside Boss Mode).
- **Affects:** [APP_FLOW.md §8.2.4](../APP_FLOW.md#824-step-4--sub-agent-specialist-execution), [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop)
- **Status:** Open — needs an "Agent Output Contract" spec, likely as a new section in TRD or a new research note.

---

## UI/UX Brief

### OQ-5: Status-color naming inconsistency between App Flow and UI/UX Brief

- **Location:** [App Flow §9](../APP_FLOW.md#component-architecture) describes Pulse Badge states as `COPPER ACTIVE` (Green) / `SUB-AGENT RUNNING` (Blue) / `VRAM HOT-SWAPPING` (Yellow) / `CRASHED` (Red). [UI/UX Brief §3.1](../UI_UX_BRIEF.md#31-pulse-badge) maps these to `system_status` values `IDLE` / `PROCESSING` / `HOT-SWAPPING` / `CRASHED`.
- **Issue:** `system_status` in the [Backend Schema §11](../BACKEND_SCHEMA.md#11-statejson--active-state-schema) example is `"PROCESSING"` — but it's unclear whether `IDLE` and `PROCESSING` are the actual enum values used by `engine.py`, or whether the UI/UX Brief introduced new naming that doesn't match what `update_telemetry()` actually writes (which only ever sets `"PROCESSING"` or `"CRASHED"` in the current `engine.py` listing).
- **Affects:** [UI_UX_BRIEF.md §3.1](../UI_UX_BRIEF.md#31-pulse-badge), [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop) (`update_telemetry`)
- **Status:** Open — needs a canonical `system_status` enum defined in [Backend Schema](../BACKEND_SCHEMA.md), and `update_telemetry()` updated to emit `IDLE` / `HOT-SWAPPING` at the appropriate points in the loop (currently it only ever sets `PROCESSING`/`CRASHED`).

---

## Resolved

_(Move items here once closed, with a pointer to the resolution.)_

- None yet.
