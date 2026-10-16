#!/usr/bin/env python3
"""
C.O.P.P.E.R. Ollama Model Readiness & First-Run Provisioner

Ensures that the local Ollama instance has at least one working base model
(e.g., llama3.2:3b or local registered GGUF) ready before the first chat session,
preventing empty-model runtime failures for non-technical users on fresh installations.

Usage:
    python scripts/models/ensure_ollama_models.py --status
    python scripts/models/ensure_ollama_models.py --auto
    python scripts/models/ensure_ollama_models.py --pull llama3.2:3b
"""

import argparse
import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
AI_MODELS_DIR = ROOT_DIR / "ai-models"
CORE_MODELS_DIR = AI_MODELS_DIR / "core"
DEFAULT_STARTER_MODEL = "llama3.2:3b"
FALLBACK_LIGHTWEIGHT_MODEL = "llama3.2:1b"
OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"


def check_ollama_server() -> bool:
    """Verifies that the Ollama daemon is responsive on 127.0.0.1:11434."""
    try:
        req = urllib.request.Request(OLLAMA_TAGS_URL, headers={"User-Agent": "COPPER-ModelProvisioner"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


def get_available_ollama_models() -> list[str]:
    """Fetches list of model tags currently registered in Ollama."""
    try:
        req = urllib.request.Request(OLLAMA_TAGS_URL, headers={"User-Agent": "COPPER-ModelProvisioner"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [m.get("name", "") for m in data.get("models", []) if m.get("name")]
    except Exception:
        return []


def check_local_gguf_files() -> list[Path]:
    """Scans ai-models/core for downloaded GGUF files."""
    if not CORE_MODELS_DIR.exists():
        return []
    return list(CORE_MODELS_DIR.glob("*.gguf"))


def register_local_models() -> bool:
    """Executes register_ollama_models.py if GGUFs are present."""
    reg_script = ROOT_DIR / "scripts" / "models" / "register_ollama_models.py"
    if reg_script.exists():
        print("[*] Local GGUF models detected. Registering into Ollama...", flush=True)
        res = subprocess.run([sys.executable, str(reg_script)], check=False)
        return res.returncode == 0
    return False


def pull_starter_model(model_name: str = DEFAULT_STARTER_MODEL) -> bool:
    """Pulls a baseline model via ollama CLI."""
    ollama_bin = shutil.which("ollama")
    if not ollama_bin:
        print("[-] Error: 'ollama' binary was not found on system PATH.", file=sys.stderr)
        return False

    print(f"[*] Pulling starter model '{model_name}' via Ollama...", flush=True)
    try:
        proc = subprocess.run([ollama_bin, "pull", model_name], check=True)
        print(f"[+] Successfully pulled '{model_name}'.", flush=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Failed to pull '{model_name}': {e}", file=sys.stderr)
        if model_name != FALLBACK_LIGHTWEIGHT_MODEL:
            print(f"[*] Attempting ultra-lightweight fallback '{FALLBACK_LIGHTWEIGHT_MODEL}'...", flush=True)
            return pull_starter_model(FALLBACK_LIGHTWEIGHT_MODEL)
        return False


def ensure_ready(auto_pull: bool = False, model_name: str = DEFAULT_STARTER_MODEL) -> dict:
    """End-to-end readiness verification and automatic first-run model resolution."""
    print("=" * 65)
    print("  C.O.P.P.E.R. LOCAL MODEL READINESS & FIRST-RUN PROVISIONER")
    print("=" * 65)

    is_running = check_ollama_server()
    if not is_running:
        print("[-] Warning: Ollama daemon is not responding on 127.0.0.1:11434.")
        print("    Please run 'ollama serve' or start Ollama Desktop before chatting.")
        return {"ready": False, "reason": "ollama_not_running", "models": []}

    models = get_available_ollama_models()
    local_ggufs = check_local_gguf_files()

    print(f"[*] Ollama Status:  ACTIVE (127.0.0.1:11434)")
    print(f"[*] Active Models:  {len(models)} registered ({', '.join(models[:4]) if models else 'None'})")
    print(f"[*] Local GGUFs:    {len(local_ggufs)} found in ai-models/core/")

    # 1. If Ollama already has working models, we are ready
    if models:
        print("\n[+] Verification PASSED: C.O.P.P.E.R. has active models available.")
        print("=" * 65)
        return {"ready": True, "models": models}

    # 2. If local GGUF models exist, register them
    if local_ggufs:
        registered = register_local_models()
        models = get_available_ollama_models()
        if models:
            print("\n[+] Verification PASSED: Successfully registered local GGUF models.")
            print("=" * 65)
            return {"ready": True, "models": models}

    # 3. No models installed anywhere: prompt or auto-pull
    print("\n[!] No active local models found.")
    if auto_pull:
        success = pull_starter_model(model_name)
        models = get_available_ollama_models()
        return {"ready": success, "models": models}

    # Prompt user interactively if in terminal
    if sys.stdin.isatty():
        choice = input(f"\n[?] Would you like to pull the default starter model '{model_name}' now? [Y/n]: ").strip().lower()
        if choice in ("", "y", "yes"):
            success = pull_starter_model(model_name)
            models = get_available_ollama_models()
            return {"ready": success, "models": models}

    print(f"\n[-] Notice: To enable local chat, run: ollama pull {model_name}")
    print("=" * 65)
    return {"ready": False, "reason": "no_models_installed", "models": []}


def main():
    parser = argparse.ArgumentParser(description="C.O.P.P.E.R. Local Model Provisioner")
    parser.add_argument("--status", action="store_true", help="Check model status without pulling")
    parser.add_argument("--auto", action="store_true", help="Automatically pull starter model if missing")
    parser.add_argument("--pull", type=str, help="Specify custom model to pull (e.g. llama3.2:3b)")
    args = parser.parse_args()

    if args.pull:
        pull_starter_model(args.pull)
        sys.exit(0)

    res = ensure_ready(auto_pull=args.auto)
    sys.exit(0 if res.get("ready") else 1)


if __name__ == "__main__":
    main()
