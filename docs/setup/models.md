# C.O.P.P.E.R. Model Setup & Management Guide (v3.0 - RTX 5060 8GB VRAM)

Tailored for modern hardware with **NVIDIA RTX 5060 (8GB VRAM)**, **AMD Ryzen 9**, and **16GB–32GB System RAM** running **Quantized Lossless Abliterated 14B GGUFs**, **Resident Mini Reflex Models**, **Local Diffusion (PICASSO)**, and **openWakeWord / Kokoro Audio Pipelines**.

---

## 1. Model Store Architecture & Manifest

All models reside under the local [`ai-models/`](./) directory, orchestrated dynamically via [`ai-models/models_manifest.json`](./models_manifest.json):

```
ai-models/
├── core/                  # 12B–14B Heavy Cognitive Models (ATLAS, VULCAN, PROMETHEUS, SCRIBE, DAEMON)
├── subagents/             # 6 Resident Mini Reflex Models (AEGIS, MERCURY, FORGE, WARDEN, CRUCIBLE, CHRONOS, ORACLE)
├── vision/                # Desktop Vision Model (ARGUS / Qwen2.5-VL 3B)
├── image/                 # 100% Offline 1-Step Local Diffusion (PICASSO / SD-Turbo)
├── embeddings/            # ChromaDB Dense Vectors (nomic-embed-text, ModernBERT, BGE Reranker)
├── audio/                 # Kokoro-82M ONNX TTS, Silero VAD v5, Whisper Large v3 Turbo
└── wakeword/              # openWakeWord Acoustic Models (hey_copper.onnx, embedding_model.onnx)
```

---

## 2. Hardware VRAM Discipline (8GB Budget)

With **8GB VRAM**, running multiple heavy models simultaneously would cause Out-Of-Memory (OOM) crashes. C.O.P.P.E.R. v3.0 enforces strict **Dynamic VRAM Tiering**:

1. **Always-On Resident Reflex Fleet (`Qwen2.5-1.5B`)**:
   - Pinned in VRAM with `keep_alive: -1` (~0.94 GB VRAM footprint).
   - Handles sub-30ms intent classification, firewall security, and translation without waking heavy models.
2. **Dynamic Heavyweight Tier (12B–14B Core Models)**:
   - Exactly ONE active 14B model slot loaded on-demand (~5.2–6.4 GB VRAM).
   - Offloads 44/49 layers to GPU, remainder to system RAM.
   - Automatically unloaded by `ModelTierManager` after 60s of idle time.
3. **Ambient Audio & Wake-Word Layer**:
   - Silero VAD v5 and openWakeWord run strictly on CPU (~1-3% CPU usage, 0 MB VRAM).

---

## 3. Automated Model Registration for Local GGUFs

To register downloaded GGUFs into your local Ollama instance automatically:

```powershell
python scripts/models/register_ollama_models.py
```

Or test all agent models with targeted prompts:

```powershell
python scripts/models/test_agents.py --all
```

---

## 4. Model Store Integrity Verification

Run the built-in integrity verifier to validate model files and storage health across all categories:

```powershell
python scripts/models/test_agents.py --list
```
