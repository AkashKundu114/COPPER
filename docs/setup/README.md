# Setup & Deployment Guide

> **Documentation hub:** [docs/README.md](../README.md) · **Related:** [Implementation Guide §16](../IMPLEMENTATION.md#16-deployment--setup) · [PRD §5](../PRD.md#5-hardware-constraints--performance-targets)

This guide consolidates [Implementation Guide §16](../IMPLEMENTATION.md#16-deployment--setup) into a step-by-step walkthrough, with a pre-flight hardware checklist and troubleshooting section. The underlying scripts/config (`setup.sh`, `requirements.txt`, the Ollama Modelfile) are defined in the Implementation Guide — this document is the *procedure*, not a duplicate source of truth for the *contents*.

---

## 1. Pre-Flight Checklist

Before running anything, confirm your machine meets the targets in [PRD §5](../PRD.md#5-hardware-constraints--performance-targets):

- [ ] GPU with **≥ 6 GB VRAM** (NVIDIA, CUDA-capable — required for Ollama GPU acceleration)
- [ ] **≥ 16 GB system RAM**
- [ ] Python **3.11+**
- [ ] Node.js (for the React frontend in `frontend/`)
- [ ] ~10–15 GB free disk space (model weights for Model 1–5, plus LoRA adapters)
- [ ] Internet access for the **initial** model pulls only ([PRD §2.1 Vision](../PRD.md#21-vision-statement): no internet dependency for core tasks thereafter)

---

## 2. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

Verify it's running:

```bash
ollama --version
curl http://localhost:11434/api/tags
```

If the second command fails, see [Troubleshooting §6.1](#61-ollama-not-reachable).

---

## 3. Pull Required Models

Per [TRD §6.2](../TRD.md#62-the-6-model-specialist-architecture), pull the Model 2, 3, and 5 base models (Model 1 and Model 4 are larger/optional and may be pulled separately depending on which agents you intend to use first):

```bash
ollama pull qwen2.5-coder:7b-q4_k_m   # Model 2: Code Engineering
ollama pull qwen2.5:3b-q4_k_m         # Model 3: OS Executors
ollama pull qwen2.5:7b-q4_k_m         # Model 5: Web & Streaming
```

> **Model 1** (`qwen2.5-14b:q4_k_m` or the DeepSeek-R1-Distill equivalent) and **Model 4** (Florence-2 / Qwen2-VL-7B) require additional setup — see [research/model-selection.md](../research/model-selection.md) for the current tradeoffs before pulling these, particularly given the [Florence-2/Ollama open question](../research/open-questions.md#oq-3-florence-2--ollama-integration).

---

## 4. Initialize the SQLite Database

```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('copper.db')
# Execute all CREATE TABLE and CREATE INDEX statements
# from Backend Schema §12 (sessions, chat_history,
# agent_execution_logs, agent_profiles, episodic_memory,
# temporal_tasks, tracking_control, + indexes)
conn.commit(); conn.close()
print('copper.db initialized.')
"
```

The full set of `CREATE TABLE` / `CREATE INDEX` statements is in [Backend Schema §12](../BACKEND_SCHEMA.md#12-sqlite-database-schema-copperdb) (§12.1–12.8). Run all of them in order — `agent_profiles` (§12.4) should be seeded immediately after creation using the personality data in [PRD Appendix A](../PRD.md#appendix-a-agent-personality-reference) and [Appendix B](../PRD.md#appendix-b-peer-rivalry-matrix).

> ⚠️ Before seeding `agent_profiles`, resolve [OQ-1: Duplicate `NEXUS` agent](../research/open-questions.md#oq-1-duplicate-nexus-agent-in-the-30-agent-roster) — inserting both `NEXUS` roster entries as-is will violate the `agent_id` primary key.

---

## 5. Install Python Dependencies

```bash
pip install -r requirements.txt --break-system-packages
playwright install chromium
```

See [Implementation Guide §16.1](../IMPLEMENTATION.md#161-prerequisites) for the full dependency list and version floors.

---

## 6. Configure Ollama Context Caps

Apply the Modelfile parameters from [Implementation Guide §16.3](../IMPLEMENTATION.md#163-ollama-model-configuration-modelfile) to **every** Model 1–5 profile, not just the example shown (Qwen2.5-Coder):

```
PARAMETER num_ctx 4096
PARAMETER keep_alive 0
```

This enforces [TRD §7.2 TR-02](../TRD.md#72-tr-02-context-window-enforcement) and [TRD §7.1 TR-01](../TRD.md#71-tr-01-model-lifecycle-management) at the model-config level, as a second line of defense beyond the per-request `options` in [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop).

---

## 7. Start Background Daemons

```bash
python3 clock_daemon.py &
python3 kinetic_daemon.py &
```

Each daemon's RAM ceiling is enforced per [TRD §7.7](../TRD.md#77-tr-07-background-daemon-requirements) — monitor with `ps` / `htop` after startup to confirm they're within budget (`clock_daemon.py` ≤ 15 MB, `kinetic_daemon.py` ≤ 20 MB).

---

## 8. Start the Frontend

```bash
cd frontend && npm install && npm run dev &
```

This serves the React + Tailwind dashboard described in [UI/UX Brief](../UI_UX_BRIEF.md), polling `state.json` via the local bridge API documented in [api/README.md](../api/README.md).

---

## 9. Run the Core Engine

```bash
python3 engine.py
```

At this point the system is live: submitting a prompt via the dashboard's Prompt Input (or `Alt+Space`) should trigger the full [App Flow §8](../APP_FLOW.md#8-primary-execution-flow-state-persistent-hot-swap) hot-swap cycle.

---

## One-Shot Script

All of the above (steps 2, 3 partial, 5, 7, 8) is automated by `setup.sh` — see [Implementation Guide §16.2](../IMPLEMENTATION.md#162-initial-setup-commands) for the full script. Run it from the project root:

```bash
bash setup.sh
```

Steps 4 (database init) and 6 (Modelfile configuration) currently require manual attention per the notes above.

---

## 10. Troubleshooting

### 6.1 Ollama not reachable

If `curl http://localhost:11434/api/tags` fails:

- Confirm the Ollama service is running (`systemctl status ollama` on Linux, or check the system tray on Windows)
- Confirm no firewall rule is blocking `localhost:11434`

### 6.2 VRAM not returning to 0 MB after a hot-swap

- Confirm `keep_alive: 0` is present in **both** the per-request `options` ([Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop)) and the Modelfile (`PARAMETER keep_alive 0`, [step 6](#6-configure-ollama-context-caps))
- Confirm `flush_vram()` is being called in the `finally` block of the main loop, not just on success — see [Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop)
- If VRAM still doesn't release, this may indicate a `torch.cuda` allocation outside Ollama's process (e.g. a stray Florence-2 subprocess — see [OQ-3](../research/open-questions.md#oq-3-florence-2--ollama-integration))

### 6.3 `state.json` corruption / malformed state errors

- Per [TRD §7.4 TR-04](../TRD.md#74-tr-04-state-file-integrity), `state.json` must be written via the atomic temp-file-then-rename pattern in `write_state()` ([Implementation Guide §14.1](../IMPLEMENTATION.md#141-main-orchestration-loop)). If you've manually edited `state.json` while `engine.py` was running, restore from the last `execution_logs` entry or delete the file — `read_state()` falls back to a safe default (`{"next_agent": "COPPER", ...}`).

### 6.4 Model pull failures / disk space

- Each Q4_K_M 7B model is roughly 4–5 GB on disk; the full Model 1–5 set plus LoRA adapters can exceed 25 GB. Re-check the pre-flight disk space checklist if `ollama pull` fails partway through.

### 6.5 Background daemon RAM exceeds budget

- If `clock_daemon.py` or `kinetic_daemon.py` exceed their [TRD §7.7](../TRD.md#77-tr-07-background-daemon-requirements) ceilings, check for accumulating in-memory state across polling cycles (e.g. an ever-growing list of fired alarms that should have been marked `is_completed = 1` in `temporal_tasks`).
