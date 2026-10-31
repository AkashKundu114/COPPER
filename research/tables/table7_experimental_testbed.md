# Table 7: Empirical Hardware and Software Testbed Specification

| System Parameter | Physical Testbed Configuration | Notes & Verification |
| :--- | :--- | :--- |
| **Host Processor** | AMD Ryzen 9 8940HX | 16 physical cores, 32 hardware threads, 4.0–5.2 GHz boost |
| **Host Memory** | 16 GB DDR5-5600 MHz | Dual-channel SODIMM |
| **Graphics Hardware** | NVIDIA GeForce RTX 5060 Laptop GPU | Ada/Blackwell mobile silicon, PCIe 4.0 x8 |
| **GPU Video Memory** | 8,151 MiB GDDR6 VRAM | 128-bit memory bus width |
| **CUDA Runtime** | CUDA 13.4 / cuDNN 9.1 | Driver version: 572.16 |
| **Operating System** | Microsoft Windows 11 Enterprise x64 | Build 26100.3194 |
| **Python Runtime** | Python 3.14.6 x64 | CPython build, MSC v.1944 64 bit |
| **Local LLM Server** | Ollama v0.5.1 | Loopback IPv4 direct connection (`127.0.0.1:11434`) |
| **Evaluated Model** | Qwen2.5-0.5B-Instruct | `q4_k_m` quantization, 100% offloaded to GPU VRAM |
| **Embedding Engine** | Local Dense 384-d Cosine + Sparse BM25 | Hybrid RRF fusion with rank constant $k=60$ |
| **Database Engine** | SQLite 3.45.1 | WAL Mode (`PRAGMA journal_mode=WAL`), `synchronous = NORMAL` |
