# C.O.P.P.E.R. Model Setup & Management Guide (v3.0 - RTX 5060 8GB VRAM)

Tailored for modern hardware with **NVIDIA RTX 5060 (8GB VRAM)**, **AMD Ryzen 9**, and **16GB–32GB System RAM** running **Quantized Lossless Abliterated 14B GGUFs**, **Resident Mini Reflex Models**, **Local Diffusion (PICASSO)**, and **openWakeWord / Kokoro Audio Pipelines**.

---

## 1. Model Store Architecture & Manifest

C.O.P.P.E.R. operates on a clean **Hybrid Model Architecture**:

1. **LLM & Reasoning Models (Managed by Ollama Engine):**
   - Core cognitive models (ATLAS 14B, VULCAN 14B, PROMETHEUS 14B, SCRIBE 14B, DAEMON 12B) and resident mini models (AEGIS, MERCURY, FORGE, WARDEN) are managed through the local **Ollama daemon** (`http://localhost:11434`).
   - Weights reside in the active Ollama library directory (e.g., `D:\Ollama\Models\blobs`), eliminating redundant duplicate GGUF copies in workspace folders.
   - Dynamic routing and VRAM lifecycle tiering are declared in [`ai-models/models_manifest.json`](../../ai-models/models_manifest.json).

2. **Multimodal, Voice & Vision Assets (Stored in `ai-models/`):**
   Non-Ollama specialized models run directly via ONNX / Torch runtimes and are housed in `ai-models/`:
   ```
   ai-models/
   ├── models_manifest.json   # Central Agent Registry & Ollama Tag Mapping
   ├── audio/                 # Kokoro-82M ONNX TTS, Silero VAD v5, Whisper Large v3 Turbo
   │   ├── tts/               # Kokoro & Piper neural voice models
   │   ├── vad/               # Silero voice activity detection
   │   └── whisper/           # Whisper speech-to-text models
   ├── image/                 # SD-Turbo safetensors offline 1-step diffusion
   └── wakeword/              # "Hey Copper" openWakeWord ONNX acoustic models
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
