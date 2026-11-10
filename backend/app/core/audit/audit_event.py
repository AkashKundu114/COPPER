"""Unified Cryptographic Audit Event Model for C.O.P.P.E.R.

Implements immutable, verifiable, and tamper-evident event structures with
SHA-256 cryptographic hash chaining and cross-system correlation identifiers.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class AuditCategory(str, Enum):
    AUTH_LOGIN = "auth_login"
    AGENT_ACTIVATED = "agent_activated"
    AGENT_DELEGATED = "agent_delegated"
    TOOL_EXECUTED = "tool_executed"
    GUARDIAN_CHALLENGE = "guardian_challenge"
    GUARDIAN_SAFETY_BLOCK = "guardian_safety_block"
    MEMORY_MUTATION = "memory_mutation"
    PRIVACY_ERASURE = "privacy_erasure"
    CONFIG_CHANGED = "config_changed"
    SANDBOX_EXECUTION = "sandbox_execution"
    DATA_EXPORT = "data_export"


class AuditOutcome(str, Enum):
    SUCCESS = "SUCCESS"
    CHALLENGED = "CHALLENGED"
    BLOCKED = "BLOCKED"
    FAILED = "FAILED"


GENESIS_HASH: str = "0000000000000000000000000000000000000000000000000000000000000000"


@dataclass
class AuditEvent:
    sequence_num: int
    category: AuditCategory
    actor: str
    action: str
    target_resource: str
    outcome: AuditOutcome
    prev_hash: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    session_id: str = "default"
    model_name: str | None = None
    operator_approved: bool = False
    trace_id: str | None = None
    span_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    entry_hash: str = ""

    def calculate_entry_hash(self) -> str:
        """Computes deterministic SHA-256 digest of this block chained to its predecessor."""
        canonical_payload = {
            "sequence_num": self.sequence_num,
            "timestamp": round(self.timestamp, 4),
            "event_id": self.event_id,
            "category": self.category.value,
            "actor": self.actor,
            "action": self.action,
            "target_resource": self.target_resource,
            "outcome": self.outcome.value,
            "session_id": self.session_id,
            "model_name": self.model_name or "",
            "operator_approved": self.operator_approved,
            "trace_id": self.trace_id or "",
            "prev_hash": self.prev_hash,
            "metadata": self.metadata,
        }
        serialized = json.dumps(canonical_payload, sort_keys=True)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def seal(self) -> None:
        """Calculates and stores the entry hash, sealing the record."""
        self.entry_hash = self.calculate_entry_hash()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["category"] = self.category.value
        data["outcome"] = self.outcome.value
        return data

    @classmethod
    def create_genesis(cls) -> AuditEvent:
        """Initializes the deterministic root Genesis block of the audit log."""
        genesis = cls(
            sequence_num=0,
            category=AuditCategory.CONFIG_CHANGED,
            actor="SYSTEM_ROOT",
            action="INITIALIZE_AUDIT_LEDGER",
            target_resource="audit_ledger",
            outcome=AuditOutcome.SUCCESS,
            prev_hash=GENESIS_HASH,
            timestamp=1700000000.0,
            event_id="00000000-0000-0000-0000-000000000000",
            metadata={"standard": "COPPER_CRYPTOGRAPHIC_AUDIT_v1"},
        )
        genesis.seal()
        return genesis
