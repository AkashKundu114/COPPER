"""Dynamic Configuration Change & Rollback Manager for C.O.P.P.E.R.

Enforces pre-activation validation, atomic hot-reload, immutable snapshot
history, and safe rollback for application configuration updates.
"""

from __future__ import annotations

import copy
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from pydantic import ValidationError

from app.core.configuration.schemas import COPPERConfig, master_config
from app.core.logger import logger


@dataclass
class ConfigChangeAuditRecord:
    timestamp: float
    operator: str
    property_path: str
    previous_value: Any
    new_value: Any
    success: bool
    error: str | None = None


@dataclass
class ConfigSnapshot:
    snapshot_id: str
    timestamp: float
    config_state: COPPERConfig
    reason: str


class ConfigChangeManager:
    """Manages safe, validated, and auditable mutations to the master configuration."""

    def __init__(self, current_config: COPPERConfig | None = None, max_snapshots: int = 20):
        self._config = current_config or master_config
        self.max_snapshots = max_snapshots
        self._snapshots: list[ConfigSnapshot] = []
        self._audit_log: list[ConfigChangeAuditRecord] = []
        self._take_snapshot("Initial boot configuration")

    @property
    def config(self) -> COPPERConfig:
        return self._config

    def _take_snapshot(self, reason: str) -> str:
        snap_id = f"snap_{int(time.time() * 1000)}"
        snapshot = ConfigSnapshot(
            snapshot_id=snap_id,
            timestamp=time.time(),
            config_state=copy.deepcopy(self._config),
            reason=reason,
        )
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self.max_snapshots:
            self._snapshots.pop(0)
        return snap_id

    def update_property(
        self,
        domain: str,
        property_name: str,
        new_value: Any,
        operator: str = "system",
    ) -> tuple[bool, str]:
        """Pre-validates and applies a configuration change atomically."""
        if not hasattr(self._config, domain):
            msg = f"Unknown configuration domain: '{domain}'"
            self._record_audit(operator, f"{domain}.{property_name}", None, new_value, False, msg)
            return False, msg

        domain_obj = getattr(self._config, domain)
        if not hasattr(domain_obj, property_name):
            msg = f"Unknown property '{property_name}' in domain '{domain}'"
            self._record_audit(operator, f"{domain}.{property_name}", None, new_value, False, msg)
            return False, msg

        prev_val = getattr(domain_obj, property_name)

        # 1. Pre-activation validation using Pydantic clone
        try:
            domain_cls = type(domain_obj)
            curr_dict = domain_obj.model_dump()
            curr_dict[property_name] = new_value
            validated_domain = domain_cls(**curr_dict)
        except ValidationError as ve:
            err_msg = f"Validation failed for {domain}.{property_name}: {ve}"
            logger.warning(f"[ConfigChangeManager] {err_msg}")
            self._record_audit(operator, f"{domain}.{property_name}", prev_val, new_value, False, err_msg)
            return False, err_msg

        # 2. Take pre-change snapshot for rollback
        self._take_snapshot(f"Pre-change snapshot before updating {domain}.{property_name}")

        # 3. Apply change
        setattr(domain_obj, property_name, getattr(validated_domain, property_name))
        self._record_audit(operator, f"{domain}.{property_name}", prev_val, new_value, True, None)
        logger.info(f"[ConfigChangeManager] Updated {domain}.{property_name}: {prev_val} -> {new_value} by {operator}")
        return True, "Configuration property updated successfully"

    def rollback(self) -> tuple[bool, str]:
        """Rolls back configuration to the previous snapshot state."""
        if len(self._snapshots) <= 1:
            return False, "No previous configuration snapshot available for rollback"

        # Pop current snapshot and restore previous
        current = self._snapshots.pop()
        target = self._snapshots[-1]
        self._config = copy.deepcopy(target.config_state)
        logger.warning(f"[ConfigChangeManager] Rolled back configuration to snapshot {target.snapshot_id} ('{target.reason}')")
        return True, f"Configuration rolled back to snapshot {target.snapshot_id}"

    def _record_audit(
        self,
        operator: str,
        path: str,
        prev: Any,
        new: Any,
        success: bool,
        error: str | None,
    ) -> None:
        self._audit_log.append(
            ConfigChangeAuditRecord(
                timestamp=time.time(),
                operator=operator,
                property_path=path,
                previous_value=prev,
                new_value=new,
                success=success,
                error=error,
            )
        )

    def get_audit_log(self) -> list[dict[str, Any]]:
        return [asdict(r) for r in self._audit_log]


config_change_manager = ConfigChangeManager()
