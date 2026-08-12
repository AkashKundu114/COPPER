# COPPER

**Centralized Omnifunctional Personal Productivity and Execution Routine**

A persistent, adaptive, guardian-style personal AI assistant. COPPER helps plan,
execute, code, and maintain routines over time — respecting your autonomy while
protecting your long-term interests.

> **Status:** Reconciled architecture (see `REVAMP_PLAN.md` in this drop for the
> full decision record). The old `docs/` folder described a different,
> superseded local-only architecture and has been removed —
> run `scripts/cleanup_deprecated_docs.sh` after merging.

---

## What COPPER is

- **Guardian, not a dictator.** Ordinary decisions are yours. When COPPER has
  strong evidence a request conflicts with your own goals, it says so
  (Levels 0–3: execute / suggest / challenge / safety-boundary) instead of
  silently complying or silently refusing.
- **Model-agnostic.** Ollama (local) is the default provider; OpenAI (cloud) is
  available per-request, and every cloud call passes through a data firewall
  that classifies and redacts sensitive content before it leaves the machine.
- **Memory with epistemics.** What COPPER "knows" about you is typed as a
  Fact, Observation, or Hypothesis, each with a confidence score and evidence
  count — never presented as more certain than it is.
- **Hot-swappable agents.** Each agent (Planner, Coding, Automation, Reminder,
  Research, Vision, …) is versioned. Activation is gated by a health check,
  and rollback restores the previous version without data loss.
- **Self-healing.** Failed tool/agent calls retry, then fall back to
  alternative tools/models/agents, before ever surfacing an unrecovered
  failure to you — and every attempt is written to the audit log.
- **Transparent by default.** Every consequential action, external API call,
  and agent change lands in a human-readable Security Center audit log, with
  one-click data export and delete-all.

## Stack

FastAPI · LangChain · PostgreSQL · Redis · ChromaDB · Ollama (backend)
React · TypeScript · Tailwind · Zustand · Tauri (frontend)

## Structure

```
backend/app/
  core/            guardian.py, data_firewall.py, self_healing.py, config.py, logger.py
  database/models/ memory_v2.py, agent_registry.py, audit_log.py, (+ existing models)
  services/        chat_service.py, guardian_service.py, (+ existing services)
  ai/              agents/, llm/, memory/, orchestration/, vision/, voice/
  api/routes/      chat.py, guardian.py, agents.py, audit.py, (+ existing routes)
frontend/src/
  pages/           AgentRegistry.tsx, SecurityCenter.tsx, Insights.tsx, (+ existing pages)
  components/chat/ GuardianChallengeModal.tsx, (+ existing chat components)
```

## Getting started

```bash
git clone <this-repo>
cd copper
docker-compose up -d postgres redis chromadb ollama
cd backend && pip install -r requirements.txt --break-system-packages
alembic upgrade head
uvicorn app.main:app --reload
```

```bash
cd frontend && npm install && npm run dev
```

## Revamp history

This repository went through a five-pass reconciliation resolving conflicts
between the original implementation, a deprecated local-only `docs/` spec, and
two new product prompts (guardian behavior + UI). Each pass is documented in
its own `PASS{n}_NOTES.md`; the top-level decisions are in `REVAMP_PLAN.md`.

## License

MIT — see `LICENSE`.
