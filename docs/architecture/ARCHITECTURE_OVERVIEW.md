# C.O.P.P.E.R. Architecture Overview

**Centralized Omnifunctional Personal Productivity and Execution Routine**  
*"Autonomous, 100% Offline Personal AI Companion, Multi-Agent Orchestrator & Desktop Guardian"*

---

## 1. System Vision & Core Operating Principles

C.O.P.P.E.R. is an autonomous, adaptive, guardian-style personal AI operating environment. It operates **100% offline by default**, combining persistent user epistemic memory, intelligent scheduling, code engineering in isolated sandboxes, multimodal voice interaction, multi-agent orchestration, and human-in-the-loop control.

### Core Architectural Principles

1. **Local-First & Zero Egress:** Executes entirely on local hardware (AMD Ryzen 9 / RTX 5060) utilizing quantized GGUF & ONNX models. Zero cloud transmission occurs by default.
2. **Multi-Tier Agent Hierarchy:** Routes queries through sub-millisecond intent classifiers to 4 heavy core models (7B–8B), 2 multimodal vision models (2B/7B), and 14 specialized micro-subagents (360M–3B).
3. **Guardian Alignment (Levels 0–3):** Evaluates prompt safety, commitment conflicts, and destructive triggers prior to execution, protecting user goals while preserving autonomy.
4. **Zero-Trust Data Firewall:** Automated real-time regex sanitization masking sensitive credentials (`sk-`, `sk-proj-`), JWT tokens, SSNs, credit cards, emails, and private IP addresses.
5. **Continuous Dynamic Routing Memory:** Self-training token-similarity memory cache (`DynamicRoutingMemory`) providing sub-0.05ms dispatch for known and evolving user intents.

---

## 2. System Architecture Diagram

```
                                  ┌───────────────────────────┐
                                  │  Electron Desktop App     │
                                  │  (React 19 + Tailwind CSS)│
                                  └─────────────┬─────────────┘
                                                │
                                    REST API / WebSockets
                                                ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ FASTAPI BACKEND (Python 3.11+ / 100% Local Execution)                                       │
│                                                                                             │
│  ┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐  │
│  │ Cascaded Agent Router   │ ──> │ Guardian Safety Engine │ ──> │ Zero-Trust Firewall    │  │
│  │ (Stage 0 Memory -> 1B)  │     │ (Levels 0 - 3 Checks)  │     │ (PII & Secret Redact)  │  │
│  └────────────┬────────────┘     └────────────────────────┘     └───────────┬────────────┘  │
│               │                                                             │               │
│               └──────────────────────────────┬──────────────────────────────┘               │
│                                              ▼                                              │
│  ┌─────────────────────────┐     ┌────────────────────────┐     ┌────────────────────────┐  │
│  │ AXIS Software Engineer  │ ──> │ Forge Sandbox Engine   │ ──> │ Local AI Model Pool    │  │
│  │ (Coding Agent)          │     │ (Isolated Execution)   │     │ (26 GGUF / ONNX Models)│  │
│  └────────────┬────────────┘     └────────────────────────┘     └───────────┬────────────┘  │
│               │                                                             │               │
│               ▼                                                             ▼               │
│  ┌─────────────────────────┐                                    ┌────────────────────────┐  │
│  │ Epistemic Fact Engine   │                                    │ Offline Audio Pipeline │  │
│  │ (Memory & Context)      │                                    │ (Whisper STT / Piper)  │  │
│  └────────────┬────────────┘                                    └────────────────────────┘  │
└───────────────┼─────────────────────────────────────────────────────────────┼───────────────┘
                │                                                             │
                ▼                                                             ▼
┌────────────────────────────────┐ ┌───────────────────────────────┐ ┌────────────────────────┐
│ PostgreSQL / SQLite Database   │ │ Redis Pub/Sub & Session Cache │ │ ChromaDB Vector Index  │
│ (Audit Logs, Episodes, History)│ │ (6379 / Memory LRU)           │ │ (8192-Token Embeddings)│
└────────────────────────────────┘ └───────────────────────────────┘ └────────────────────────┘
```

---

## 3. Desktop Application Navigation Architecture

The desktop application is built on **Electron** with strict in-app navigation guards (no external browser escapes) and a persistent 13-section sidebar:

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
- **Level 0 (Execute):** Direct task execution for safe, non-destructive read actions.
- **Level 1 (Suggest):** Inline optimization tips (e.g. recommending vectorized operations or indexed queries).
- **Level 2 (Challenge):** Interactive modal presenting clear reasons, evidence points, and risk assessments for commitment conflicts.
- **Level 3 (Safety Boundary):** Strict block on irreversible operations (`rm -rf`, raw disk partitioning, database deletion) requiring explicit case-sensitive confirmation.

### 4.2 Cascaded Multi-Tier Router
1. **Stage 0 (Exact & Token Similarity Memory):** Instant retrieval (< 0.05ms) from dynamically cached exemplars.
2. **Stage 1 (High-Precision Regex & Pattern Suppression):** Deterministic routing for coding keywords, system administration, calendar scheduling, and media queries.
3. **Stage 2 (Micro-LLM Intent Classifier):** Llama-3.2-1B / Qwen2.5-0.5B fallback for complex conversational nuances.

### 4.3 Forge Sandbox Engine
- Isolated execution environment for code synthesis.
- Enforces configurable subprocess timeouts (10s default), environment variable isolation, and automatic cleanup of temporary execution artifacts.
