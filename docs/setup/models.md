# C.O.P.P.E.R. Model Setup & Management Guide (RTX 5060 8GB VRAM Optimized)

Tailored for modern laptops with **NVIDIA RTX 5060 (8GB VRAM)**, **AMD Ryzen 9**, and **16GB–32GB System RAM** running **Q4_K_M Lossless Abliterated GGUF models**, **Local Diffusion (PICASSO)**, and **openWakeWord / Kokoro Audio Pipelines**.

---

## 1. Model Store Architecture & Manifest

All models reside under the local [`ai-models/`](file:///d:/C.O.P.P.E.R/ai-models/) directory, orchestrated dynamically via [`ai-models/models_manifest.json`](file:///d:/C.O.P.P.E.R/ai-models/models_manifest.json):

```
ai-models/
├── core/                  # Lossless Abliterated 7B/8B Heavyweight Models (Chat, Coding, Docs, Reasoning, Auto)
├── subagents/             # 14 Specialized Micro-Subagents (Router, Firewall, Diagnostics, Git, SQL, etc.)
├── vision/                # Multimodal Vision Models (Qwen2.5-VL 7B & 3B)
├── image/                 # 100% Offline 1-Step Local Diffusion (PICASSO / SD-Turbo)
├── embeddings/            # ChromaDB Dense Vectors (nomic-embed-text, ModernBERT, BGE Reranker)
├── audio/                 # Kokoro-82M ONNX TTS, Silero VAD v5, Whisper Large v3 Turbo
└── wakeword/              # openWakeWord Acoustic Models (hey_copper.onnx, embedding_model.onnx)
```

---

## 2. Hardware VRAM Discipline (8GB Budget)

With **8GB VRAM**, running multiple heavy models simultaneously would cause Out-Of-Memory (OOM) crashes. C.O.P.P.E.R. enforces strict **VRAM Tiering**:

1. **Always-On Gatekeeper / Router (`Llama-3.2-1B-abliterated` / `Qwen2.5-0.5B-abliterated`)**:
   - Pinned in VRAM with `keep_alive: -1` (~770 MB VRAM footprint).
   - Handles sub-40ms intent classification, wake-word validation, and small reflex replies.
2. **Transient Heavyweight Tier (7B–8B Core Models)**:
   - Loaded on-demand into GPU VRAM (4.0–4.6 GB).
   - Automatically unloaded by `ModelTierManager` after 60s–240s of idle time.
3. **Ambient Audio & Wake-Word Layer**:
   - Silero VAD v5 and openWakeWord run strictly on CPU ($\approx 1-3\%$ CPU usage, 0 MB VRAM).

---

## 3. Ollama Modelfile Creation for Local GGUFs

To register downloaded GGUFs into your local Ollama instance, create a `Modelfile`:

```dockerfile
# Example Modelfile for AXIS Coding Agent
FROM ./ai-models/core/Qwen2.5-Coder-7B-Instruct-abliterated-Q4_K_M.gguf
PARAMETER temperature 0.2
PARAMETER top_p 0.95
PARAMETER stop "<|im_end|>"
PARAMETER stop "<|endoftext|>"
```

Then create and verify the model:
```bash
ollama create qwen2.5-coder-abliterated:7b -f Modelfile
ollama list
```

---

## 4. Model Store Integrity Verification

Run the built-in integrity verifier to validate all 34 model files and storage health across all categories:

```powershell
python scripts/models/verify_models.py
```
