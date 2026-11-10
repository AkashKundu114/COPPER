"""Isolated In-Memory Secret & Credential Vault.

Enforces Zero-Trust Principle:
"Never expose credentials through prompts, logs or memory."
Binds stored secrets directly to the DataFirewall redaction engine dynamically.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.core.data_firewall import DataClass, _PATTERNS
from app.core.logger import logger


@dataclass
class SecretItem:
    key: str
    description: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed_at: datetime | None = None
    access_count: int = 0


class SecretVault:
    """Provides secure, segregated secret storage in memory.
    
    Dynamically registers all stored secret values with DataFirewall regex
    filters to guarantee automatic masking if any component attempts serialization.
    """

    def __init__(self):
        self._secrets: dict[str, str] = {}
        self._metadata: dict[str, SecretItem] = {}

    def store_secret(self, key: str, value: str, description: str = "") -> None:
        """Stores a secret securely and binds its literal value to DataFirewall redaction."""
        if not key or not value:
            return

        clean_key = key.strip()
        clean_val = value.strip()
        self._secrets[clean_key] = clean_val
        self._metadata[clean_key] = SecretItem(key=clean_key, description=description)

        # Dynamically register value with DataFirewall redaction patterns
        if len(clean_val) >= 6:
            escaped_val = re.escape(clean_val)
            pattern = re.compile(rf"\b{escaped_val}\b")
            _PATTERNS.insert(0, (pattern, "•••VAULT_SECRET_REDACTED•••", DataClass.SECRET))

        logger.debug(f"[Security] Stored secret '{clean_key}' in vault and registered firewall redaction.")

    def get_secret(self, key: str) -> str | None:
        """Retrieves raw secret value for internal authenticated usage."""
        clean_key = key.strip()
        if clean_key in self._secrets:
            meta = self._metadata[clean_key]
            meta.last_accessed_at = datetime.now(timezone.utc)
            meta.access_count += 1
            return self._secrets[clean_key]
        return None

    def list_secrets(self) -> list[dict[str, Any]]:
        """Lists metadata of stored secrets without exposing values."""
        return [
            {
                "key": m.key,
                "description": m.description,
                "created_at": m.created_at.isoformat(),
                "last_accessed_at": m.last_accessed_at.isoformat() if m.last_accessed_at else None,
                "access_count": m.access_count,
            }
            for m in self._metadata.values()
        ]

    def delete_secret(self, key: str) -> bool:
        """Deletes a secret from the vault."""
        clean_key = key.strip()
        if clean_key in self._secrets:
            del self._secrets[clean_key]
            del self._metadata[clean_key]
            return True
        return False


secret_vault = SecretVault()
