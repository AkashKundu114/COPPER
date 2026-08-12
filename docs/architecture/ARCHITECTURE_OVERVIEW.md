# C.O.P.P.E.R. Architecture Overview

**Centralized Omnifunctional Personal Productivity and Execution Routine**

---

## 1. System Vision & Core Principles

C.O.P.P.E.R. is a persistent, adaptive, guardian-style personal AI assistant designed to help users plan, execute tasks, write code, and maintain routines over time. Unlike conventional chat assistants that silently obey or rigidly refuse, C.O.P.P.E.R. operates with an epistemic memory model and an adaptive intervention framework (Levels 0–3).

### Key Architectural Pillars

1. **Guardian Autonomy Gating:** Evaluates user prompts against short-term goals and long-term user wellbeing. Provides graduated responses from direct execution (Level 0) to safety boundaries (Level 3).
2. **Model Agnostic & Privacy First:** Operates locally by default (via Ollama). External calls (e.g., OpenAI, Claude) pass through a zero-trust **Data Firewall** for classification, masking, and redaction before data leaves the local machine.
3. **Epistemic Memory Hierarchy:** Differentiates between *Facts*, *Observations*, and *Hypotheses*, each tagged with confidence scores, evidence counts, and decay rates.
4. **Hot-Swappable Versioned Agents:** Houses 30 specialized agents (Planner, Coding, Automation, Research, Vision, etc.) managed via a dynamic registry with automated health checks and instant rollback capabilities.
5. **Self-Healing Execution Loop:** Retries failed tool calls, falls back to secondary tools/models/agents, and records every failure and recovery attempt in an immutable Security Center Audit Log.

---

## 2. High-Level System Architecture

```
                                  +-----------------------+
                                  |   Tauri Desktop /     |
                                  |   React Web Frontend  |
                                  +-----------+-----------+
                                              |
                                   REST / WebSockets
                                              v
+-----------------------------------------------------------------------------------+
| FASTAPI BACKEND (Python)                                                          |
|                                                                                   |
|  +-------------------+      +--------------------+      +----------------------+  |
|  | Agent Router      | ---> | Guardian Engine    | ---> | Data Firewall        |  |
|  | (Keyword & Vector)|      | (Levels 0 - 3)     |      | (PII Redaction)      |  |
|  +-------------------+      +--------------------+      +----------+-----------+  |
|                                                                    |              |
|  +-----------------------------------------------------------------+              |
|  v                                                                                |
|  +-------------------+      +--------------------+      +----------------------+  |
|  | Agent Orchestrator| ---> | Self-Healing Loop  | ---> | LLM Service Layer    |  |
|  | (30 Specialized)  |      | (Fallback & Retry) |      | (Ollama / Cloud)     |  |
|  +---------+---------+      +--------------------+      +----------+-----------+  |
|            |                                                       |              |
|            v                                                       |              |
|  +-------------------+                                             |              |
|  | Epistemic Learner |                                             |              |
|  | & Fact Engine     |                                             |              |
|  +---------+---------+                                             |              |
+------------|-------------------------------------------------------|--------------+
             |                                                       |
             v                                                       v
+------------------------+  +----------------------+  +-----------------------------+
| PostgreSQL / SQLite    |  | Redis Cache & PubSub |  | ChromaDB Vector Store       |
| (Memory, Registry, Logs)|  | (State, Live Events) |  | (Semantic Embedding Index)  |
+------------------------+  +----------------------+  +-----------------------------+
```

---

## 3. Core Subsystems

### 3.1 Guardian Engine
The Guardian Engine evaluates user instructions before execution.
- **Level 0 (Direct Execution):** Standard task request aligning with goals.
- **Level 1 (Nudge / Suggestion):** Minor conflict with schedule or routine; offers alternative suggestions while proceeding.
- **Level 2 (Challenge / Friction):** Moderate conflict (e.g., scheduling a late-night heavy task after noting fatigue); requires explicit user confirmation via the `GuardianChallengeModal`.
- **Level 3 (Safety Boundary):** Severe violation of long-term interests or system constraints; halts execution cleanly with explanation.

### 3.2 Data Firewall
Protects sensitive personal information from escaping local boundaries.
- **Scanner:** Regex and heuristic PII detectors (API keys, SSNs, phone numbers, private project code).
- **Transformer:** Masks detected entities into synthetic tokens (`[REDACTED_API_KEY_1]`).
- **Unmasker:** Re-hydrates response stream when returning results from cloud endpoints.

### 3.3 Epistemic Memory System
Stores user information with strict evidence metrics rather than flat key-value pairs:
- **Facts:** High-confidence verified truths (e.g., "User uses Windows 11").
- **Observations:** Single or few-instance occurrences (e.g., "User worked past 1 AM on Tuesday").
- **Hypotheses:** Inferred behavioral patterns awaiting decay validation or reinforcement (e.g., "User prefers dark mode interfaces").

### 3.4 Agent Registry & Orchestrator
- Houses 30 specialized domain agents organized across 4 primary tiers:
  - **Core Reasoning Tier:** System planning, decision trees, guardian validation.
  - **Task Execution Tier:** Code synthesis, file system operations, script automation.
  - **Specialized Knowledge Tier:** Research, data analysis, document parsing.
  - **Interface & Audio Tier:** Speech simulation, vision input, layout generation.
- Supports runtime hot-swapping: Versioning agents independently, health checking before deployment, and instantaneous rollback.

### 3.5 Self-Healing Execution Loop
When an agent action encounters an exception (tool failure, LLM context timeout, invalid format):
1. **Retry Phase:** Executes exponential backoff retry with adjusted temperature/parameters.
2. **Tool Fallback:** Switches to secondary tools or alternative bash/python utilities.
3. **Model Fallback:** Switches from local Ollama model to cloud model if local context overflows.
4. **Audit Recording:** Logged to Audit Trail with diagnostic error frames and resolution paths.

---

## 4. Communication & Protocol Specs

- **REST API (`/api/v1`):** Synchronous operations including system config, agent registry querying, audit log retrieval, memory inspection, and CRUD.
- **WebSockets (`/ws/chat`):** Bi-directional streaming for live chat responses, real-time neural visualizer event streaming (`copper_thinking`, `route_decision`, `edge_pulse`, `agent_active`, `agent_speaking`, `memory_update`), and Guardian intervention triggers.

---

## 5. Technology Stack Summary

| Domain | Selected Technology | Rationale |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.11+ / FastAPI | High throughput async I/O, native ML/LLM library support. |
| **Relational Database** | PostgreSQL / SQLite | Acid-compliant memory persistence, JSONB support. |
| **Cache & Queue** | Redis | Ephemeral session state, WebSocket pub/sub backplane. |
| **Vector Index** | ChromaDB | Local, lightweight embeddings index for RAG memory search. |
| **Local LLM Engine** | Ollama | Private local inference supporting Llama 3, Qwen, Mistral. |
| **Cloud LLM Providers**| OpenAI / Anthropic | Optional cloud fallback via Data Firewall. |
| **Frontend UI** | React 18 / TypeScript / Vite | Declarative component model, strict typing. |
| **Desktop Shell** | Tauri | Lightweight native desktop bundle with direct OS integration. |
| **Styling** | Tailwind CSS / Vanilla CSS | Molten Copper design language & custom SVG visualizer. |
