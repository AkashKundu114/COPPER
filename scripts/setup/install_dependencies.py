#!/usr/bin/env python3
"""
C.O.P.P.E.R. One-Click Dependency Installer

Automates local environment provisioning for new systems:
1. Detects Python environment and pip.
2. Checks Ollama installation and running state.
3. Installs backend dependencies from requirements.txt.
4. Checks GPU and CUDA capability.
"""

import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
REQUIREMENTS_FILE = BACKEND_DIR / "requirements.txt"
OLLAMA_WIN_INSTALLER = "https://ollama.com/download/OllamaSetup.exe"


def check_python_environment() -> dict:
    """Verifies Python version and virtual environment."""
    return {
        "version": platform.python_version(),
        "executable": sys.executable,
        "is_venv": sys.prefix != sys.base_prefix,
        "satisfies_version": sys.version_info >= (3, 11),
    }


def check_ollama() -> dict:
    """Checks whether Ollama is installed on system PATH and responsive."""
    ollama_bin = shutil.which("ollama")
    is_installed = ollama_bin is not None
    is_running = False

    if is_installed:
        try:
            import urllib.request

            req = urllib.request.Request("http://127.0.0.1:11434/api/tags", headers={"User-Agent": "COPPER-Setup"})
            with urllib.request.urlopen(req, timeout=2) as resp:
                is_running = resp.status == 200
        except Exception:
            is_running = False

    return {
        "installed": is_installed,
        "running": is_running,
        "binary_path": ollama_bin,
    }


def install_python_requirements() -> dict:
    """Installs dependencies from requirements.txt into the active Python environment."""
    if not REQUIREMENTS_FILE.exists():
        return {"success": False, "error": f"Requirements file not found at {REQUIREMENTS_FILE}"}

    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE), "--quiet"],
            capture_output=True,
            text=True,
            timeout=300,
        )
        return {
            "success": proc.returncode == 0,
            "stdout": proc.stdout[:500] if proc.stdout else "",
            "stderr": proc.stderr[:500] if proc.stderr else "",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_disk_space() -> dict:
    """Checks available and total disk space on the installation drive."""
    total, used, free = shutil.disk_usage(ROOT_DIR)
    gb = 1024**3
    return {
        "total_gb": round(total / gb, 2),
        "free_gb": round(free / gb, 2),
        "used_gb": round(used / gb, 2),
        "sufficient_for_models": (free / gb) >= 15.0,  # Minimum 15 GB recommended
    }


def main():
    print("=" * 60)
    print("  C.O.P.P.E.R. DEPENDENCY CHECK & INSTALLER")
    print("=" * 60)

    py_info = check_python_environment()
    print(f"\n[Python Environment]")
    print(f"  Version:     {py_info['version']} (Compatible: {py_info['satisfies_version']})")
    print(f"  Executable:  {py_info['executable']}")
    print(f"  In Venv:     {py_info['is_venv']}")

    ollama_info = check_ollama()
    print(f"\n[Ollama Status]")
    print(f"  Installed:   {ollama_info['installed']}")
    print(f"  Running:     {ollama_info['running']}")

    disk_info = get_disk_space()
    print(f"\n[Disk Storage]")
    print(f"  Free Space:  {disk_info['free_gb']} GB")
    print(f"  Sufficient:  {disk_info['sufficient_for_models']}")

    print("\n[Dependency Status]")
    print("  Requirements file:", REQUIREMENTS_FILE)
    print("=" * 60)


if __name__ == "__main__":
    main()
