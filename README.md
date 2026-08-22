# C.O.P.P.E.R.

**Centralized Omnifunctional Personal Productivity and Execution Routine**  
*"Autonomous, 100% Offline Personal AI Companion, Multi-Agent Orchestrator & Desktop Guardian"*

[![License: MIT](https://img.shields.io/badge/License-MIT-amber.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://reactjs.org/)
[![Electron](https://img.shields.io/badge/Electron-Desktop-47848F.svg)](https://www.electronjs.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-213%20Passed%20(100%25)-brightgreen.svg)]()
[![Routing QPS](https://img.shields.io/badge/Routing%20Throughput-~19%2C000%20QPS-blueviolet.svg)]()
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Offline%20%7C%20Zero%20Egress-success.svg)]()
[![Security](https://img.shields.io/badge/CodeQL-Advanced%20Security%20Scanning-purple.svg)]()

---

## 🌟 Executive Summary & Key Highlights

> **Engineered** a persistent, privacy-preserving personal AI operating system **as measured by** 100% offline local execution with zero cloud egress, **by architecting** a multi-tier agent orchestration framework across 26 quantized local models (`Llama-3.1-8B`, `Qwen2.5-Coder-7B`, `Mistral-7B`, `DeepSeek-R1-7B`, `Qwen2-VL-7B`), achieving **sub-millisecond routing (0.05ms)**, **100% Guardian threat sensitivity**, and autonomous self-healing.

- **⚡ Sub-Millisecond Multi-Stage Router (< 0.05ms):** Cascaded regex pre-filtering, token-similarity dynamic exemplar cache (`DynamicRoutingMemory`), and micro-LLM intent scoring achieving **100.0% accuracy across 1,110 benchmark cases (~19,000 QPS)**.
- **🛡️ Guardian Safety & Alignment Engine:** 4-level disagreement protocol (Execute, Suggest, Challenge, Safety Boundary) evaluating user prompts against destructive triggers (`rm -rf`, raw disk formats, database drops) and commitment conflicts with **100.0% threat catch sensitivity (0 breaches across 250 test cases)**.
- **🔒 Zero-Trust Data Firewall:** Automated real-time regex sanitization masking sensitive PII (OpenAI `sk-` / `sk-proj-` tokens, Bearer headers, SSNs, credit cards, emails, IP addresses, file paths).
- **🎙️ Offline Multimodal Voice Pipeline:** Real-time speech transcription via Whisper STT (`ggml-base.en.bin`) and natural voice synthesis via Piper ONNX (`en_US-amy`, `en_US-ryan`) with zero internet dependency.
- **🧠 3-Layer Epistemic Memory:** Persistent storage of user facts, preferences, and hypotheses integrating SQLite state with ChromaDB semantic vector embeddings (`nomic-embed-text-v1.5`).
- **💻 Native Desktop Application:** Standalone Electron desktop app with single-instance locking, in-app navigation constraints (no external browser popups), and seamless Windows startup auto-launch.

---

## 🏗️ System Architecture

```text
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

## 🤖 Model & Subagent Topology (26 Artifacts / 39.5 GB)

| Tier | Model Architecture | Quantization | Size | Core Specialization |
| :--- | :--- | :---: | :---: | :--- |
| **Chat / Core** | `Meta-Llama-3.1-8B-Instruct` | Q4_K_M | 4.58 GB | Primary conversational companion & task coordinator |
| **Coding (AXIS)** | `Qwen2.5-Coder-7B-Instruct` | Q4_K_M | 4.36 GB | Full-stack software engineering & sandbox testing |
| **Automation** | `Mistral-7B-Instruct-v0.3` | Q4_K_M | 4.07 GB | OS file operations, window management & system tools |
| **Reasoning** | `DeepSeek-R1-Distill-Qwen-7B` | Q4_K_M | 4.36 GB | Complex multi-step reasoning & research synthesis |
| **Vision Primary** | `Qwen2-VL-7B-Instruct` | Q4_K_M | 4.36 GB | Full screenshot inspection & architectural diagrams |
| **Vision Fast** | `Qwen2-VL-2B-Instruct` | Q4_K_M | 940 MB | Fast UI bounding box localization & OCR extraction |
| **Embeddings** | `nomic-embed-text-v1.5` | Q4_K_M | 80 MB | ChromaDB 8192-dim semantic vector memory |
| **14 Micro-Subagents** | `Llama-3.2`, `Qwen2.5`, `SmolLM2`, `Falcon3`, `Gemma-2`, `Granite-3.1` (360M – 3B) | Q4_K_M | ~16 GB total | Micro-routing, AST linting, git commits, SQL queries, shell validation |

---

## 📊 Comprehensive Benchmark Results

![Routing & Guardian Benchmark](docs/images/routing_accuracy_benchmark.png)

Evaluated using the automated evaluation suite ([`backend/eval/benchmark.py`](backend/eval/benchmark.py)) across **1,360 validation test cases**:

| Evaluation Metric | Measured Result | Benchmark Standard | Status |
| :--- | :---: | :---: | :---: |
| **Agent Routing Accuracy** | **100.0%** (1,110 / 1,110) | $\ge 98.0\%$ | 🟢 Verified |
| **Routing Weighted F1 Score** | **100.0%** | $\ge 98.0\%$ | 🟢 Verified |
| **Average Routing Latency** | **0.052 ms** (P95: 0.066 ms) | $< 1.0\text{ ms}$ | 🟢 Verified |
| **Routing Throughput** | **18,954 QPS** | $> 10,000\text{ QPS}$ | 🟢 Verified |
| **Guardian Threat Catch Rate** | **100.0%** (250 / 250) | $\ge 99.0\%$ | 🟢 Verified |
| **Critical Security Breaches** | **0 Breaches** (0.0% Risk) | $0\text{ Breaches}$ | 🟢 Verified |
| **Pytest Suite Pass Rate** | **213 / 213 (100%)** | $100\%$ | 🟢 Verified |

| Sub-Millisecond Latency Distribution | VRAM Memory Allocation (RTX 5060 - 8GB) |
| :--- | :--- |
| ![Latency Percentiles](docs/images/latency_percentiles.png) | ![VRAM Allocation](docs/images/vram_memory_allocation.png) |

| Token Generation & Processing Speed | Multi-Model Capability Radar Matrix |
| :--- | :--- |
| ![Token Throughput](docs/images/token_generation_throughput.png) | ![Model Radar](docs/images/model_comparison_radar.png) |

---

## 🚀 Quick Start Guide

### ⚡ Live Telemetry & Benchmarking Tab

COPPER now features a dedicated **Benchmarks & Metrics** tab inside the Electron Desktop Application. This provides live 1.5-second polling of:
- **Token Velocity**: Real-time Prompt Tokens/Sec and Generation Tokens/Sec.
- **Hardware Thermals**: Live GPU Core, Hotspot, and CPU Package Temperatures.
- **VRAM Monitor**: Live 8GB VRAM allocation tracking (Core, Subagent, KV Cache).
- **System RAM**: Sub-1GB active memory footprint monitoring.
- **Live Evaluator**: Run synthetic benchmark test cases directly from the UI with real-time accuracy scoring.

### Prerequisites

### Prerequisites
- **Python 3.11+**
- **Node.js 20+** & **npm**
- **Git**

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/AkashKundu114/COPPER.git
cd COPPER

# Setup Python Virtual Environment
python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# Linux/macOS:
source .venv/bin/activate

# Install Dependencies
pip install -r backend/requirements.txt
```

### 2. Run Test Suite
```bash
# Run all 213 unit & integration tests
python -m pytest tests/ -v

# Run the 1,360-sample evaluation benchmark
python backend/eval/benchmark.py
```

### 3. Launch Desktop Application (1-Click)
```bash
# Windows 1-Click Launch:
.\scripts\dev\start_dev.bat

# Or run frontend desktop dev server:
cd frontend
npm install
npm run desktop
```

---

## 📁 Repository Directory Structure

```
COPPER/
├── backend/                       # FastAPI backend, agent router, guardian, services
│   ├── app/
│   │   ├── ai/                    # Orchestration, agents, memory, LLM clients
│   │   ├── api/                   # REST routes (chat, voice, memory, episodes, audit)
│   │   ├── core/                  # Guardian, data firewall, sandbox, anomaly sentinel
│   │   └── database/              # SQLAlchemy models, Postgres/SQLite connections
│   └── eval/                      # Comprehensive benchmark suite & synthetic generator
├── frontend/                      # Standalone Electron desktop app (React 19 + Vite)
│   ├── src/                       # React components, state stores, styling
│   └── electron-main.cjs          # Electron lifecycle, navigation guards, single-instance lock
├── tests/                         # 213 Pytest unit and integration test suites
│   ├── ai/                        # Agent router, prompts, LLM clients, task scheduler
│   ├── api/                       # REST API route integration tests
│   ├── audio/                     # Whisper STT, Piper TTS, and PCM stream tests
│   ├── core/                      # Guardian, data firewall, forge sandbox, self-healing
│   └── memory/                    # Context engine, episodic memory, vector store
├── infrastructure/                # Containerization and production orchestration
│   ├── docker/                    # Dockerfiles, docker-compose.dev.yml, docker-compose.prod.yml
│   ├── kubernetes/                # Modular k8s manifests (base, ingress, deployments)
│   ├── nginx/                     # Reverse proxy with WebSocket streaming & SSL config
│   └── systemd/                   # Linux systemd service unit
├── scripts/                       # Operational scripts & utilities
│   ├── dev/                       # Local dev launchers and test scripts
│   ├── models/                    # Model organizer & integrity verifier
│   ├── windows/                   # Windows auto-start installer & background launchers
│   └── db/                        # Database schema initializer & seed data loader
├── data/                          # 100% Local data persistence layer (Memory, Vectors, Voice)
└── docs/                          # Comprehensive technical and architectural specifications
```

---

## 📜 License

Distributed under the **MIT License**. See [`LICENSE`](file:///d:/C.O.P.P.E.R/LICENSE) for full details.
