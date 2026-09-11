import json
import uuid
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any
import os
from pathlib import Path

from app.core.logger import logger

@dataclass
class SyncPayload:
    payload_id: str
    device_id: str
    device_name: str
    timestamp: str
    active_project: str
    recent_tasks: List[Dict[str, Any]]
    unresolved_queries: List[str]
    memory_hash: str
    checksum: str

class DeviceSyncCoordinator:
    def __init__(self):
        self.data_dir = Path("data")
        self.sync_file = self.data_dir / "device_sync.json"
        self._ensure_data_dir()
        self.device_id = self._get_or_create_device_id()
    
    def _ensure_data_dir(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if not self.sync_file.exists():
            self._save_state({
                "device_id": str(uuid.uuid4()),
                "connected_devices": {},
                "last_sync": None
            })

    def _get_or_create_device_id(self) -> str:
        state = self._load_state()
        if "device_id" not in state:
            state["device_id"] = str(uuid.uuid4())
            self._save_state(state)
        return state["device_id"]

    def _load_state(self) -> Dict[str, Any]:
        try:
            if self.sync_file.exists():
                with open(self.sync_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading sync state: {e}")
        return {"device_id": str(uuid.uuid4()), "connected_devices": {}, "last_sync": None}

    def _save_state(self, state: Dict[str, Any]):
        try:
            with open(self.sync_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving sync state: {e}")

    def generate_handoff_payload(self, device_name: str = "Primary Rig") -> SyncPayload:
        logger.info(f"Generating handoff payload for device: {device_name}")
        payload_data = {
            "payload_id": str(uuid.uuid4()),
            "device_id": self.device_id,
            "device_name": device_name,
            "timestamp": datetime.utcnow().isoformat(),
            "active_project": "default",
            "recent_tasks": [],
            "unresolved_queries": [],
            "memory_hash": "mock_hash"
        }
        
        checksum_str = json.dumps(payload_data, sort_keys=True)
        payload_data["checksum"] = hashlib.sha256(checksum_str.encode()).hexdigest()
        
        return SyncPayload(**payload_data)

    def receive_handoff_payload(self, payload: dict) -> dict:
        logger.info(f"Receiving handoff payload from device: {payload.get('device_name')}")
        
        # Verify checksum
        provided_checksum = payload.pop("checksum", None)
        checksum_str = json.dumps(payload, sort_keys=True)
        expected_checksum = hashlib.sha256(checksum_str.encode()).hexdigest()
        
        if provided_checksum != expected_checksum:
            logger.warning("Checksum validation failed for handoff payload")
            raise ValueError("Invalid checksum")
        
        # Apply state
        state = self._load_state()
        device_id = payload.get("device_id")
        if device_id:
            state.setdefault("connected_devices", {})[device_id] = {
                "name": payload.get("device_name"),
                "last_seen": payload.get("timestamp")
            }
            state["last_sync"] = datetime.utcnow().isoformat()
            self._save_state(state)
        
        # Return back the checksum for consistency
        payload["checksum"] = provided_checksum
        return {"status": "success", "applied_payload": payload}

    def get_sync_status(self) -> dict:
        state = self._load_state()
        return {
            "current_device": self.device_id,
            "last_sync": state.get("last_sync"),
            "connected_devices": state.get("connected_devices", {}),
            "sync_health": "healthy"
        }

device_sync = DeviceSyncCoordinator()
