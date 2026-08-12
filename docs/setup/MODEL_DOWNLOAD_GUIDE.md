# C.O.P.P.E.R. Model Setup Guide (RTX 5060 8GB VRAM Optimized)

Tailored for laptops with **NVIDIA RTX 5060 (8GB VRAM)**, **AMD Ryzen 9 8940HX**, and **16GB System RAM** running **Q4_K_M** quantized GGUF models via Ollama.

---

## 🎯 Hardware Memory Strategy

With **8GB VRAM**, each Q4_K_M quantized model takes **~3.8 GB to 4.7 GB VRAM**, allowing every model to fit **100% inside GPU VRAM** with 3GB+ headroom for KV-cache context windows. Ollama switches active models in $< 1$ second automatically.

---

## 🚀 Copy & Paste Terminal Pull Commands

Run these 3 commands in your terminal for the optimal 8GB VRAM setup:

```bash
# 1. Core Reasoning & Guardian Alignment (Q4_K_M ~4.7 GB VRAM)
ollama pull llama3.1:8b

# 2. Code Synthesis, Refactoring & Debugging (Q4_K_M ~4.4 GB VRAM)
ollama pull qwen2.5-coder:7b

# 3. Epistemic Memory & Task Scheduling (Q4_K_M ~4.1 GB VRAM)
ollama pull mistral:7b-instruct
```

---

## 📋 Q4_K_M Model Allocation for RTX 5060 8GB VRAM

| Model Pull Command | Q4 VRAM Size | Expected Speed (RTX 5060) | Assigned Sub-Agents & Roles |
| :--- | :--- | :--- | :--- |
| `ollama pull llama3.1:8b` | **~4.7 GB** | **55–70 tokens/sec** | **COPPER Core**, `WARDEN` (Security), `AEGIS` (Guardian), `ATLAS` (Task Core), `DIRECTOR` (Workflow). |
| `ollama pull qwen2.5-coder:7b` | **~4.4 GB** | **65–85 tokens/sec** | `AXIS` (Coding), `CRUCIBLE` (Refactoring), `FORGE` (Build Systems), `GLITCH` (Debugging), `TENSOR` (ML Ops). |
| `ollama pull mistral:7b-instruct` | **~4.1 GB** | **70–90 tokens/sec** | `CHRONOS` (Schedule), `MNEMONIC` (Memory), `SYNAPSE` (Learner), `LEDGER` (Finance), `PIVOT` (Routines). |
| `ollama pull deepseek-coder:6.7b` *(Optional)* | **~3.8 GB** | **75–95 tokens/sec** | `QUANTA` (Data Analytics), `CYPHER` (Crypto), `PRISM` (Logic Engine), `GOLIATH` (Big Data). |
| `ollama pull llava:7b` *(Optional Vision)* | **~4.5 GB** | **50–65 tokens/sec** | `IRIS` (Vision Inspection), `SPECTRE` (UI Inspector), `RENDER` (Design Layout). |

---

## ⚙️ Recommended Ollama Environment Settings

To maximize RTX 5060 GPU utilization and prevent VRAM unloading latency, set this environment variable in your terminal or Windows System Environment Variables:

```powershell
# In Windows PowerShell:
$env:OLLAMA_NUM_PARALLEL="1"
$env:OLLAMA_KEEP_ALIVE="10m"
```

- `OLLAMA_KEEP_ALIVE="10m"`: Keeps the active model loaded in VRAM for 10 minutes so back-and-forth prompts respond instantly without reloading overhead.
- `OLLAMA_NUM_PARALLEL="1"`: Ensures 100% of the RTX 5060's VRAM is dedicated to single-user generation.
