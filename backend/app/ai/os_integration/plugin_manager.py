import json
import os
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.core.logger import logger

@dataclass
class PluginManifest:
    id: str
    name: str
    version: str
    description: str
    author: str
    category: str
    tools: List[Dict[str, Any]]
    enabled: bool
    installed_at: str

class PluginManager:
    def __init__(self):
        self.data_path = os.path.join("data", "plugins.json")
        self.plugins: Dict[str, PluginManifest] = {}
        self._ensure_data_dir()
        self.load_plugins()

    def _ensure_data_dir(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

    def load_plugins(self):
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        self.plugins[item["id"]] = PluginManifest(**item)
            except Exception as e:
                logger.error(f"Failed to load plugins from {self.data_path}: {e}")
                self._seed_default_plugins()
        else:
            self._seed_default_plugins()

    def save_plugins(self):
        try:
            with open(self.data_path, "w", encoding="utf-8") as f:
                data = [asdict(p) for p in self.plugins.values()]
                json.dump(data, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save plugins to {self.data_path}: {e}")

    def _seed_default_plugins(self):
        now = datetime.utcnow().isoformat()
        defaults = [
            PluginManifest(
                id="spotify-controller",
                name="Spotify Controller",
                version="1.0.0",
                description="Control Spotify playback.",
                author="COPPER",
                category="media",
                tools=[],
                enabled=True,
                installed_at=now
            ),
            PluginManifest(
                id="home-assistant",
                name="Home Assistant",
                version="1.0.0",
                description="Integrate with Home Assistant for IoT control.",
                author="COPPER",
                category="iot",
                tools=[],
                enabled=True,
                installed_at=now
            ),
            PluginManifest(
                id="arxiv-fetcher",
                name="Arxiv Fetcher",
                version="1.0.0",
                description="Search and fetch papers from Arxiv.",
                author="COPPER",
                category="productivity",
                tools=[],
                enabled=True,
                installed_at=now
            )
        ]
        for p in defaults:
            self.plugins[p.id] = p
        self.save_plugins()

    def list_plugins(self) -> List[PluginManifest]:
        return list(self.plugins.values())

    def install_plugin(self, manifest_dict: Dict[str, Any]) -> PluginManifest:
        manifest_dict.setdefault("enabled", True)
        manifest_dict.setdefault("installed_at", datetime.utcnow().isoformat())
        if "tools" not in manifest_dict:
            manifest_dict["tools"] = []
        plugin = PluginManifest(**manifest_dict)
        self.plugins[plugin.id] = plugin
        self.save_plugins()
        return plugin

    def toggle_plugin(self, plugin_id: str, enabled: bool) -> Optional[PluginManifest]:
        plugin = self.plugins.get(plugin_id)
        if plugin:
            plugin.enabled = enabled
            self.save_plugins()
            return plugin
        return None

    def uninstall_plugin(self, plugin_id: str) -> bool:
        if plugin_id in self.plugins:
            del self.plugins[plugin_id]
            self.save_plugins()
            return True
        return False

    def get_registered_tools(self) -> List[Dict[str, Any]]:
        tools = []
        for p in self.plugins.values():
            if p.enabled and p.tools:
                tools.extend(p.tools)
        return tools

plugin_manager = PluginManager()
