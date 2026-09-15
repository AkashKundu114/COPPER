from typing import Any

from fastapi import APIRouter, HTTPException

from app.ai.os_integration.plugin_manager import PluginManifest, plugin_manager

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("", response_model=list[PluginManifest])
async def list_plugins():
    return plugin_manager.list_plugins()


@router.post("/install", response_model=PluginManifest)
async def install_plugin(manifest_dict: dict[str, Any]):
    try:
        return plugin_manager.install_plugin(manifest_dict)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{id}/toggle", response_model=PluginManifest)
async def toggle_plugin(id: str, enabled: bool):
    plugin = plugin_manager.toggle_plugin(id, enabled)
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return plugin


@router.delete("/{id}")
async def uninstall_plugin(id: str):
    success = plugin_manager.uninstall_plugin(id)
    if not success:
        raise HTTPException(status_code=404, detail="Plugin not found")
    return {"status": "success"}


@router.get("/tools", response_model=list[dict[str, Any]])
async def get_plugin_tools():
    return plugin_manager.get_registered_tools()
