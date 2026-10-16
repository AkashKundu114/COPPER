# C.O.P.P.E.R. Known Limitations & Release Constraints

This document explicitly identifies architectural, runtime, and hardware boundaries for the `0.1.0-alpha` release.

---

## 1. Release Lifecycle & Status
- **Alpha Status**: C.O.P.P.E.R. is in active alpha development. Core architectures (agent routing, Guardian safety, epistemic memory, REST APIs) are fully functional and covered by 728 automated tests, but breaking schema changes or API migrations may occur across minor releases.
- **Single-User Target**: C.O.P.P.E.R. is engineered as a local personal operating system running on a single user's workstation. Multi-tenant access controls or user permission delegation are not implemented.

---

## 2. Model Dependencies & Inference
- **Ollama Requirement**: Live local language generation requires a running Ollama daemon (`http://localhost:11434`) with downloaded models (e.g., `qwen2.5:14b`).
- **Offline Standalone Demo Mode**: When Ollama is offline or not installed, setting `COPPER_DEMO=1` (or running `make demo`) enables a standalone evaluation mode with pre-seeded state and synthetic responses.
- **VRAM Contention on 8GB Cards**: When running heavy 14B models alongside local diffusion (SD-Turbo), VRAM headroom is tight. The built-in `VRAMPager` evicts competing models, but concurrent 14B LLM generation and image rendering is serialized.

---

## 3. Platform & Desktop Boundary
- **Reference Host**: Reference measurements and verification were conducted on Windows 11 (AMD64, 16 physical cores, 16 GB RAM, RTX 5060 Laptop GPU).
- **Cross-Platform Execution**: Backend and frontend SPA execute across Linux, macOS, and Windows. Docker images (`docker compose up`) provide containerized environments for Linux and macOS.
- **Native Electron Packages**: Electron 44 desktop shells are provided via `launch-desktop.js` and `electron-main.cjs`. Building installers for macOS or Linux requires host-platform code signing and toolchains.

---

## 4. Voice & Audio Pipeline
- **Hardware Dependent**: Wake-word detection (`openwakeword`) and microphone input (`sounddevice`) require active physical or virtual audio devices. In headless CI environments, display and audio default to mock/headless drivers.
- **Whisper & Kokoro Fallbacks**: If PyTorch or local ONNX runtime is absent, audio transcription and synthesis gracefully fall back or emit diagnostic notices.

---

## 5. Epistemic Memory Calibration
- **Decay & Pruning**: Epistemic decay runs periodically (default: 600s interval). For databases exceeding 100,000 memories, manual vacuuming or running `python scripts/wipe_data.py` may be required to maintain sub-50ms vector search latencies.
