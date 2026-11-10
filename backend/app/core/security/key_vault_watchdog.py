"""Cryptographic Key Rotation Manager & Privilege Drift Watchdog for C.O.P.P.E.R.

Coordinates zero-downtime key rotation with multi-version keyrings, verifies HMAC
signing keys, and audits active agent sessions to interdict privilege drift or creep.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger
from app.core.security.access_control import Permission, Principal, Role


@dataclass
class KeyVersion:
    version_id: int
    secret_bytes: bytes
    created_at: float
    is_active: bool = True


@dataclass
class KeyRotationReport:
    report_id: str
    timestamp: float
    active_key_version: int
    total_key_versions: int
    privilege_drift_detected: bool
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class KeyVaultWatchdog:
    """Manages key lifecycle, rotation schedules, and agent permission drift detection."""

    def __init__(self):
        self._keyring: dict[int, KeyVersion] = {}
        self._active_version: int = 1
        # Initialize primary root key
        self._keyring[1] = KeyVersion(
            version_id=1,
            secret_bytes=os.urandom(32),
            created_at=time.time(),
            is_active=True,
        )
        self._permission_baselines: dict[str, set[Permission]] = {
            "agent_coding": {Permission.TOOL_EXECUTE_SENSITIVE, Permission.TOOL_EXECUTE_SAFE, Permission.SYSTEM_READ},
            "agent_research": {Permission.MEMORY_READ, Permission.TOOL_EXECUTE_SAFE, Permission.SYSTEM_READ},
            "agent_chat": {Permission.MEMORY_READ, Permission.MEMORY_WRITE, Permission.CHAT_INTERACT},
        }

    def rotate_key(self) -> int:
        """Rotates the primary signing/encryption key, archiving previous versions for decryption."""
        new_v = self._active_version + 1
        # Deactivate old primary
        self._keyring[self._active_version].is_active = False
        # Create new primary
        self._keyring[new_v] = KeyVersion(
            version_id=new_v,
            secret_bytes=os.urandom(32),
            created_at=time.time(),
            is_active=True,
        )
        self._active_version = new_v
        logger.info(f"[KeyVaultWatchdog] Rotated encryption key to version {new_v}")
        return new_v

    def sign_payload(self, payload: str, version: int | None = None) -> tuple[str, int]:
        """Signs a payload using specified key version (defaults to active version)."""
        v = version or self._active_version
        key_bytes = self._keyring[v].secret_bytes
        sig = hmac.new(key_bytes, payload.encode("utf-8"), hashlib.sha256).hexdigest()
        return sig, v

    def verify_signature(self, payload: str, signature: str, version: int) -> bool:
        """Verifies signature against the designated key version in the keyring."""
        if version not in self._keyring:
            return False
        expected, _ = self.sign_payload(payload, version=version)
        return hmac.compare_digest(expected, signature)

    def audit_agent_privilege_drift(self, agent_id: str, requested_permissions: list[Permission]) -> bool:
        """Detects whether an agent is requesting permissions beyond its assigned baseline."""
        baseline = self._permission_baselines.get(agent_id, set())
        requested = set(requested_permissions)
        drift = requested - baseline
        if drift:
            logger.warning(
                f"[KeyVaultWatchdog] Privilege drift detected for '{agent_id}': "
                f"Attempting unauthorized permissions: {[p.name for p in drift]}"
            )
            return True
        return False

    def generate_vault_report(self) -> KeyRotationReport:
        """Generates key rotation and vault health report."""
        now = time.time()
        rep_id = f"KVR-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig, _ = self.sign_payload(f"{rep_id}:{self._active_version}:{len(self._keyring)}")

        return KeyRotationReport(
            report_id=rep_id,
            timestamp=now,
            active_key_version=self._active_version,
            total_key_versions=len(self._keyring),
            privilege_drift_detected=False,
            signature=sig,
        )


key_vault_watchdog = KeyVaultWatchdog()
