# C.O.P.P.E.R Systems Architecture & Runtime Audit

**Audit Baseline:** Git commit `ed23f11`  
**System Title:** Centralized Omnifunctional Personal Productivity and Execution Routine (C.O.P.P.E.R)  
**Lead Architect:** Principal AI Systems Engineer & Architecture Auditor (`18458884-f127-4873-8175-78d81797cc85`)  
**Status:** FULL RUNTIME MAPPING COMPLETE; IMPLEMENTATION VERIFIED  

---

## 1. System Topology & Core Subsystems

C.O.P.P.E.R is a local-first, privacy-preserving multi-agent assistant runtime.

```
+-------------------------------------------------------------------------------+
|                             CLIENT / OPERATOR INTERFACE                       |
|                 (FastAPI WebSockets, REST Endpoints, Desktop UI)              |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                            EPSTEMIC CONTEXT ENGINE                            |
|  - Temporal Context (Clock, Session, Fatigue)                                 |
|  - GraphRAG Context (NetworkX Entity-Relationship Subgraphs)                   |
|  - Persistent Memory (PostgreSQL UserMemoryV2 + ChromaDB Vector Store)        |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                        THREE-TIER HIERARCHICAL ROUTER                         |
|  - Tier 1: Deterministic Pattern & Greeting Matcher (< 0.2 ms)                |
|  - Tier 2: GPUSemanticRouter (all-MiniLM-L6-v2 Embeddings, ~8.4 ms)           |
|  - Tier 3: LLM Intent Classifier Fallback                                     |
+-------------------------------------------------------------------------------+
                                      |
                 +--------------------+--------------------+
                 v                                         v
+----------------------------------+     +--------------------------------------+
|       STANDALONE AGENT PIPELINE  |     |         TASKGRAPH ORCHESTRATION      |
|  - Chat, Research, Vision, etc.  |     |  - DAG Task Decomposition            |
|  - ReAct Tool Loop (max 5 steps) |     |  - TaskWAL Write-Ahead Logging       |
+----------------------------------+     +--------------------------------------+
                 |                                         |
                 +--------------------+--------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                            TOOL EXECUTOR & SAFETY GATE                        |
|  - ToolRegistry Schema Validation                                             |
|  - GuardianEngine Hard-Safety & Reversibility Gate                            |
|  - MemoryQuarantine Dual-Plane Authority Gate                                  |
|  - DataFirewall Inbound & Outbound Redaction                                  |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                         PHYSICAL EXECUTION ENVIRONMENT                        |
|  - Local File System (TaskWAL snapshots)                                      |
|  - Forge Sandbox (Docker / Subprocess Sanitization)                           |
|  - Screen Tools (PyAutoGUI Windows Desktop Interaction)                       |
|  - Outbound Network (Strict Airgap Enforcement)                               |
+-------------------------------------------------------------------------------+
```

---

## 2. 12-Member Active Agent Fleet

1. **`chat` (ChatAgent):** Conversational assistant, smalltalk, general reasoning.
2. **`coding` (CodingAgent):** Code generation, refactoring, linting, debugging.
3. **`automation` (AutomationAgent):** OS shell automation, script workflows.
4. **`reminder` (ReminderAgent):** Scheduled alarms, cron jobs, time-anchored tasks.
5. **`research` (ResearchAgent):** Document synthesis, arXiv academic search.
6. **`vision` (VisionAgent / IRIS):** Visual desktop interaction, closed-loop UI grounding.
7. **`planner` (PlannerAgent):** Task graph decomposition, dependency scheduling.
8. **`guardian` (GuardianAgent):** Policy enforcement, safety gating, memory authority.
9. **`web_search` (WebSearchAgent):** SearXNG queries, privacy-first web fetch.
10. **`document` (DocumentAgent):** Document formatting, PDF/Markdown synthesis.
11. **`image` (ImageAgent):** Stable Diffusion image synthesis.
12. **`self_model` (SelfModelAgent):** Epistemic reflection, user preference learning.

---

## 3. Storage & Persistence Tiers

- **Relational DB (PostgreSQL / SQLite fallback):** `UserMemoryV2`, `ChatMessage`, `ScheduledTask`, `TaskExecutionLog`.
- **Vector DB (ChromaDB):** Dense semantic embeddings for long-term memory retrieval and semantic cache.
- **Graph DB (NetworkX):** Graph RAG knowledge graph storing entities, relations, and neighborhood subgraphs.
- **Write-Ahead Log (TaskWAL):** Append-only JSONL journal logging pre-mutation snapshots for zero-loss recovery.
