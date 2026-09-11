from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.ai.os_integration.plugin_manager import plugin_manager, PluginManifest

router = APIRouter(prefix="/plugins", tags=["plugins"])

@router.get("", response_model=List[PluginManifest])
async def list_plugins():
    return plugin_manager.list_plugins()

@router.post("/install", response_model=PluginManifest)
async def install_plugin(manifest_dict: Dict[str, Any]):
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

@router.get("/tools", response_model=List[Dict[str, Any]])
async def get_plugin_tools():
    return plugin_manager.get_registered_tools()
