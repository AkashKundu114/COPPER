#!/usr/bin/env python3
"""
C.O.P.P.E.R. Model Downloader (v3.0 Sovereign Architecture)
Downloads the 5 Heavy 14B models and 6 Mini Subagent models from Hugging Face directly
into their designated folders under `ai-models/`.

Usage:
    python scripts/models/download_v3_models.py --all
    python scripts/models/download_v3_models.py --mini-only
    python scripts/models/download_v3_models.py --heavy-only
    python scripts/models/download_v3_models.py --model atlas
"""

import argparse
import os
import shutil
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download

ROOT_DIR = Path(__file__).resolve().parents[2]
AI_MODELS_DIR = ROOT_DIR / "ai-models"

# Master Model Registry for v3.0
MODELS = {
    # ── Heavyweight Cognitive Tier (14B Models, ~6.4 GB each) ─────────────────
    "atlas": {
        "agent": "ATLAS (Chat & Orchestrator)",
        "repo": "bartowski/Qwen2.5-14B-Instruct-GGUF",
        "filename": "Qwen2.5-14B-Instruct-IQ3_XS.gguf",
        "target_dir": AI_MODELS_DIR / "core",
        "target_name": "Qwen2.5-14B-Instruct-IQ3_XS.gguf",
        "tier": "heavy",
        "size_gb": 6.38,
    },
    "vulcan": {
        "agent": "VULCAN (Coding Specialist)",
        "repo": "bartowski/Qwen2.5-Coder-14B-Instruct-abliterated-GGUF",
        "filename": "Qwen2.5-Coder-14B-Instruct-abliterated-IQ3_XS.gguf",
        "target_dir": AI_MODELS_DIR / "core",
        "target_name": "Qwen2.5-Coder-14B-Instruct-abliterated-IQ3_XS.gguf",
        "tier": "heavy",
        "size_gb": 6.38,
    },
    "prometheus": {
        "agent": "PROMETHEUS (Deep Reasoning)",
        "repo": "bartowski/DeepSeek-R1-Distill-Qwen-14B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-14B-IQ3_XS.gguf",
        "target_dir": AI_MODELS_DIR / "core",
        "target_name": "DeepSeek-R1-Distill-Qwen-14B-IQ3_XS.gguf",
        "tier": "heavy",
        "size_gb": 6.38,
    },
    "scribe": {
        "agent": "SCRIBE (Document & Academic Synthesis)",
        "repo": "bartowski/phi-4-GGUF",
        "filename": "phi-4-IQ3_XS.gguf",
        "target_dir": AI_MODELS_DIR / "core",
        "target_name": "phi-4-IQ3_XS.gguf",
        "tier": "heavy",
        "size_gb": 6.24,
    },
    "daemon": {
        "agent": "DAEMON (Tool Automation)",
        "repo": "bartowski/Mistral-Nemo-Instruct-2407-GGUF",
        "filename": "Mistral-Nemo-Instruct-2407-IQ3_M.gguf",
        "target_dir": AI_MODELS_DIR / "core",
        "target_name": "Mistral-Nemo-Instruct-2407-IQ3_M.gguf",
        "tier": "heavy",
        "size_gb": 5.72,
    },

    # ── Lightweight Subagent Tier (<=2B Models, ~1 GB each) ───────────────────
    "mercury": {
        "agent": "MERCURY & AEGIS (Router & Firewall)",
        "repo": "Qwen/Qwen2.5-1.5B-Instruct-GGUF",
        "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "target_dir": AI_MODELS_DIR / "subagents" / "router",
        "target_name": "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf",
        "copy_to": [AI_MODELS_DIR / "subagents" / "firewall" / "Qwen2.5-1.5B-Instruct-Q4_K_M.gguf"],
        "tier": "mini",
        "size_gb": 0.94,
    },
    "forge": {
        "agent": "FORGE & WARDEN (Code Linter & Shell Safety)",
        "repo": "Qwen/Qwen2.5-Coder-3B-Instruct-GGUF",
        "filename": "qwen2.5-coder-3b-instruct-q4_k_m.gguf",
        "target_dir": AI_MODELS_DIR / "subagents" / "coding",
        "target_name": "Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf",
        "copy_to": [AI_MODELS_DIR / "subagents" / "shell" / "Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf"],
        "tier": "mini",
        "size_gb": 1.80,
    },
    "crucible": {
        "agent": "CRUCIBLE (Traceback Diagnostician & Planner)",
        "repo": "unsloth/DeepSeek-R1-Distill-Qwen-1.5B-GGUF",
        "filename": "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "target_dir": AI_MODELS_DIR / "subagents" / "diagnostics",
        "target_name": "DeepSeek-R1-Distill-Qwen-1.5B-Q4_K_M.gguf",
        "tier": "mini",
        "size_gb": 1.04,
    },
    "chronos": {
        "agent": "CHRONOS & SPIDER (Memory & DOM Cleaner)",
        "repo": "HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF",
        "filename": "smollm2-1.7b-instruct-q4_k_m.gguf",
        "target_dir": AI_MODELS_DIR / "subagents" / "memory",
        "target_name": "SmolLM2-1.7B-Instruct-Q4_K_M.gguf",
        "tier": "mini",
        "size_gb": 1.00,
    },
    "oracle": {
        "agent": "ORACLE (SQL & Schema Guard)",
        "repo": "ibm-research/granite-3.2-2b-instruct-GGUF",
        "filename": "granite-3.2-2b-instruct-Q4_K_M.gguf",
        "target_dir": AI_MODELS_DIR / "subagents" / "sql",
        "target_name": "granite-3.2-2b-instruct-Q4_K_M.gguf",
        "tier": "mini",
        "size_gb": 1.44,
    },
    "argus": {
        "agent": "ARGUS (Desktop Vision Eye)",
        "repo": "unsloth/Qwen2.5-VL-3B-Instruct-GGUF",
        "filename": "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf",
        "target_dir": AI_MODELS_DIR / "vision",
        "target_name": "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf",
        "tier": "mini",
        "size_gb": 2.10,
    },
}


def download_single_model(key: str, conf: dict) -> bool:
    print("\n" + "=" * 70)
    print(f"[*] Processing: {conf['agent']}")
    print(f"    - Source:   {conf['repo']}/{conf['filename']}")
    print(f"    - Size:     ~{conf['size_gb']} GB")

    target_path = conf["target_dir"] / conf["target_name"]
    conf["target_dir"].mkdir(parents=True, exist_ok=True)

    if target_path.exists() and target_path.stat().st_size > 1024 * 1024 * 100:
        actual_gb = round(target_path.stat().st_size / (1024**3), 2)
        print(f"[+] Already downloaded: {target_path} ({actual_gb} GB). Skipping download.")
    else:
        print(f"[>] Streaming download to cache...")
        try:
            downloaded_file = hf_hub_download(
                repo_id=conf["repo"],
                filename=conf["filename"],
                resume_download=True,
            )
            print(f"[>] Copying to destination: {target_path}")
            shutil.copyfile(downloaded_file, target_path)
            print(f"[+] Successfully placed {conf['target_name']}")
        except Exception as e:
            print(f"[!] Download failed for {key}: {e}")
            return False

    # Handle linked / shared weight copies
    if "copy_to" in conf:
        for copy_dest in conf["copy_to"]:
            copy_dest.parent.mkdir(parents=True, exist_ok=True)
            if not copy_dest.exists():
                print(f"    [+] Linking shared model to {copy_dest.name}...")
                try:
                    shutil.copyfile(target_path, copy_dest)
                except Exception as e:
                    print(f"    [!] Failed to copy shared model: {e}")

    return True


def main():
    parser = argparse.ArgumentParser(description="Download v3.0 AI models for C.O.P.P.E.R.")
    parser.add_argument("--all", action="store_true", help="Download all 11 models (~39 GB total)")
    parser.add_argument("--mini-only", action="store_true", help="Download only the 6 fast mini models (~8.3 GB)")
    parser.add_argument("--heavy-only", action="store_true", help="Download only the 5 14B heavy models (~31 GB)")
    parser.add_argument("--model", type=str, choices=list(MODELS.keys()), help="Download a specific model by key")
    parser.add_argument("--list", action="store_true", help="List all available models and their statuses")

    args = parser.parse_args()

    if args.list or len(sys.argv) == 1:
        print("\n=== C.O.P.P.E.R. v3.0 MODEL INVENTORY ===")
        for key, conf in MODELS.items():
            path = conf["target_dir"] / conf["target_name"]
            status = f"[PRESENT] ({round(path.stat().st_size / 1024**3, 2)} GB)" if path.exists() else "[MISSING]"
            print(f"{key:<12} | {conf['tier'].upper():<5} | ~{conf['size_gb']:<4} GB | {status:<18} | {conf['agent']}")
        print("\nRun with --mini-only, --heavy-only, --all, or --model <key> to start downloading.")
        return

    to_download = []
    if args.model:
        to_download.append((args.model, MODELS[args.model]))
    elif args.mini_only:
        to_download = [(k, v) for k, v in MODELS.items() if v["tier"] == "mini"]
    elif args.heavy_only:
        to_download = [(k, v) for k, v in MODELS.items() if v["tier"] == "heavy"]
    elif args.all:
        to_download = list(MODELS.items())

    print(f"\n[*] Starting download of {len(to_download)} models for C.O.P.P.E.R...")
    success_count = 0
    for key, conf in to_download:
        if download_single_model(key, conf):
            success_count += 1

    print("\n" + "=" * 70)
    print(f"[+] Download phase complete: {success_count}/{len(to_download)} models ready.")
    print("=" * 70)


if __name__ == "__main__":
    main()
