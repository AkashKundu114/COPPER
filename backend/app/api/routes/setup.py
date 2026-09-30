"""
FastAPI REST endpoints for the C.O.P.P.E.R. First-Run Setup Wizard,
system requirement diagnostics, and dependency management.
"""

import json
from pathlib import Path
import shutil
import sys
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException
import httpx
from pydantic import BaseModel, Field

from app.ai.llm.model_manager import model_manager
from app.core.gpu_activation import detect_gpu

router = APIRouter(prefix="/api/setup", tags=["setup"])

SETUP_STATE_FILE = Path.home() / ".copper" / "setup_state.json"


class SetupStatePayload(BaseModel):
    completed: bool = False
    current_step: int = 1
    selected_preset: str = "recommended"  # "minimal" | "recommended" | "full"
    selected_agents: list[str] = Field(default_factory=list)
    selected_voice: str = "af_bella"
    selected_image_model: str = "sd_turbo"
    models_installed: list[str] = Field(default_factory=list)


class PullModelRequest(BaseModel):
    model_tag: str = Field(..., description="Ollama model tag e.g. 'qwen2.5:1.5b'")


def _load_setup_state() -> dict[str, Any]:
    if SETUP_STATE_FILE.exists():
        try:
            with open(SETUP_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "completed": False,
        "current_step": 1,
        "selected_preset": "recommended",
        "selected_agents": [
            "chat",
            "coding",
            "research",
            "vision",
            "guardian",
            "reminder",
            "planner",
            "automation",
        ],
        "selected_voice": "af_bella",
        "selected_image_model": "sd_turbo",
        "models_installed": [],
    }


def _save_setup_state(state: dict[str, Any]) -> None:
    SETUP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETUP_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


@router.get("/state", summary="Get wizard state")
def get_state() -> dict[str, Any]:
    """Returns the persistent onboarding setup state."""
    return _load_setup_state()


@router.post("/state", summary="Save wizard state")
def save_state(payload: SetupStatePayload) -> dict[str, Any]:
    """Updates the onboarding setup state."""
    state = payload.dict()
    _save_setup_state(state)
    return {"success": True, "state": state}


@router.get("/system-check", summary="System requirements verification")
async def system_check() -> dict[str, Any]:
    """Performs pre-flight checks on host GPU, disk, Python, and Ollama."""
    # 1. GPU Check
    gpu = detect_gpu()

    # 2. Disk Space Check
    install_path = Path(__file__).resolve().parent.parent.parent.parent.parent
    try:
        total, used, free = shutil.disk_usage(install_path)
        free_gb = round(free / (1024**3), 2)
        total_gb = round(total / (1024**3), 2)
    except Exception:
        free_gb = 50.0
        total_gb = 500.0

    # 3. Ollama Check
    ollama_installed = shutil.which("ollama") is not None
    ollama_running = False
    ollama_models: list[str] = []

    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            res = await client.get("http://127.0.0.1:11434/api/tags")
            if res.status_code == 200:
                ollama_running = True
                models_data = res.json().get("models", [])
                ollama_models = [m.get("name", "") for m in models_data if m.get("name")]
    except Exception:
        ollama_running = False

    return {
        "ready": (ollama_running or ollama_installed) and free_gb >= 10.0,
        "gpu": gpu,
        "disk": {
            "free_gb": free_gb,
            "total_gb": total_gb,
            "sufficient": free_gb >= 15.0,
        },
        "python": {
            "version": sys.version.split()[0],
            "executable": sys.executable,
            "compatible": sys.version_info >= (3, 11),
        },
        "ollama": {
            "installed": ollama_installed,
            "running": ollama_running,
            "installed_models": ollama_models,
        },
    }


@router.get("/models/manifest", summary="Available model catalog")
def get_model_catalog() -> dict[str, Any]:
    """Returns the model catalog extracted from the models manifest."""
    manifest = model_manager.manifest
    return {
        "always_on_mini_model": manifest.get("always_on_mini_model", {}),
        "core_agents": manifest.get("core_agents", {}),
        "subagents": manifest.get("subagents", {}),
        "vision_agents": manifest.get("vision_agents", {}),
        "audio": manifest.get("audio", {}),
        "image_studio": manifest.get("image_studio", {}),
    }


@router.post("/pull-model", summary="Pull Ollama model tag")
async def pull_model(req: PullModelRequest) -> dict[str, Any]:
    """Instructs local Ollama instance to pull the requested model tag."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.post(
                "http://127.0.0.1:11434/api/pull",
                json={"name": req.model_tag, "stream": False},
            )
            if res.status_code in (200, 201):
                return {"success": True, "model": req.model_tag, "status": "pulled"}
            return {"success": False, "status_code": res.status_code, "error": res.text}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to communicate with Ollama daemon at http://127.0.0.1:11434: {e}",
        )
