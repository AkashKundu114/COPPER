# C.O.P.P.E.R. Architecture Overview

**Centralized Omnifunctional Personal Productivity and Execution Routine**
*"Your Personal AI Operating System"*

---

## 1. System Vision & Core Operating Principles

C.O.P.P.E.R. is a persistent, adaptive, guardian-style personal AI operating environment. It operates **100% offline by default**, combining persistent user memory, daily scheduling, productivity management, coding assistance, behavioral tracking, multi-agent orchestration, and human-in-the-loop control.

### Core Philosophical Principles

1. **Understand & Remember:** Maintains an epistemic user model (Facts, Observations, Hypotheses) with Bayesian confidence updates and evidence tracking.
2. **Execute & Protect:** Operates locally via Ollama and pre-trained open models. Zero cloud transmission occurs unless the user explicitly enables cloud fallback.
3. **Guardian Alignment (Levels 0–3):** Operates as a guardian, not a dictator. Evaluates prompt safety and schedule conflicts, challenging risky actions while respecting ordinary user autonomy.
4. **State Multi-Layering:** Combines `state.json` (live session state), SQLite (persistent relational memory), and LangGraph (execution state).
5. **Self-Healing & Evaluated Improvement:** Recovers automatically from tool failures, tracks incidents in the Security Center Audit Log, and benchmarks candidate models before deployment.

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
| FASTAPI BACKEND (Python 3.11+ / Local-First)                                       |
|                                                                                   |
|  +-------------------+      +--------------------+      +----------------------+  |
|  | Agent Router      | ---> | Guardian Engine    | ---> | Data Firewall        |  |
|  | (Pre-trained Pool)|      | (Levels 0 - 3)     |      | (PII Redaction)      |  |
|  +-------------------+      +--------------------+      +----------+-----------+  |
|                                                                    |              |
|  +-----------------------------------------------------------------+              |
|  v                                                                                |
|  +-------------------+      +--------------------+      +----------------------+  |
|  | Agent Orchestrator| ---> | Self-Healing Loop  | ---> | Pre-Trained Models   |  |
|  | (30 Specialized)  |      | (Fallback & Retry) |      | (Ollama / Local LLM) |  |
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
| SQLite Persistence     |  | Redis Cache & PubSub |  | ChromaDB Vector Store       |
| (state.json + 14 DBs)  |  | (Session & Events)   |  | (Local Embedding Index)     |
+------------------------+  +----------------------+  +-----------------------------+
```

---

## 3. Desktop Application Navigation Architecture

The desktop application UI is structured around a persistent 13-section left sidebar:

```
┌────────────────────────────────────────────────────────────────────────┐
│ COPPER                       ● Local   🔒 Private   🎙 Ready  [Profile]│
├──────────────┬─────────────────────────────────────────────────────────┤
│ ❖ Logo       │                                                         │
│ 📊 Dashboard │                                                         │
│ 💬 Chat      │                    MAIN WORKSPACE                       │
│ 📅 Today     │                                                         │
│ ☑ Tasks      │    (Interactive Views: Neural Brain Ganglia Map,        │
│ 📁 Projects  │     Schedule Timeline, Memory Inspector, Security       │
│ 🧠 Memory    │     Center Audit Log, Self-Improvement Benchmark)      │
│ 🤖 Agents    │                                                         │
│ 📈 Activity  │                                                         │
│ 💡 Insights  │                                                         │
│ ⚡ Self-Impr │                                                         │
│ 🛡️ Security  │                                                         │
│ ⚙️ Settings  │                                                         │
└──────────────┴─────────────────────────────────────────────────────────┘
```

---

## 4. Core Subsystems

### 4.1 Guardian Engine & Disagreement Protocol
Evaluates instructions against schedule commitments, energy fatigue, and long-term user goals:
- **Level 0 (Execute):** Direct task execution.
- **Level 1 (Suggest):** Inline optimization tips.
- **Level 2 (Challenge):** Interactive `GuardianChallengeModal` presenting clear reasons, evidence bullet points, confidence level, recommendation, and options ([Follow recommendation], [Proceed anyway], [Discuss]).
- **Level 3 (Safety Boundary):** Clean halt with limitation explanation and safe alternatives.

### 4.2 Zero-Trust Data Firewall
- **100% Offline Default:** Prevents unauthorized network egress.
- **PII Detection:** Scans outgoing prompts for API keys (`sk-••••`), SSNs, credit cards, emails, and private source code.
- **Token Anonymization:** Replaces detected entities with synthetic tokens (`[REDACTED_API_KEY_1]`).

### 4.3 Epistemic Memory Engine
Categorizes user knowledge into three confidence tiers:
- **Fact ($C \ge 0.85$):** Verified explicit truths.
- **Observation ($0.50 \le C < 0.85$):** Derived from repeated behavior.
- **Hypothesis ($0.10 \le C < 0.50$):** Tentative pattern inferences.

### 4.4 State Management Layers
1. `state.json`: Human-readable live session state.
2. `SQLite`: Persistent relational database storing `users`, `goals`, `projects`, `tasks`, `schedules`, `memories`, `conversations`, `experiences`, `agent_runs`, `tool_calls`, `evaluations`, `agent_versions`, `incidents`, `training_examples`.
3. `LangGraph State`: Dynamic execution graph state.

---

## 5. Technology Stack Summary

| Layer | Selected Technology | Offline Capability |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.11+ / FastAPI / LangGraph | 100% Local / Offline |
| **Database & State** | SQLite (`copper_memory.db`) + `state.json` | 100% Local / Offline |
| **Vector Engine** | ChromaDB (In-Process) | 100% Local / Offline |
| **Cache & PubSub** | Redis 7 | 100% Local / Offline |
| **LLM Inference** | Ollama (Llama 3.1 8B, Qwen 2.5 Coder, Mistral 7B) | 100% Local / Offline |
| **Frontend UI** | React 18 / TypeScript / Vite / Tailwind | 100% Local / Offline |
| **Desktop Shell** | Tauri v2 (Rust desktop wrapper) | 100% Local / Offline |
