"""Cryptographic Audit Service for C.O.P.P.E.R.

Thread-safe, transaction-consistent append-only audit event logging service.
Serializes hash chaining using an asynchronous lock to prevent concurrency race conditions.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any

from app.core.audit.audit_event import AuditCategory, AuditEvent, AuditOutcome
from app.core.audit.verifier import AuditIntegrityVerifier, VerificationResult
from app.core.logger import logger


class AuditService:
    """Central cryptographic audit ledger coordinator."""

    def __init__(self):
        self._events: list[AuditEvent] = []
        self._chain_lock = asyncio.Lock()
        self._seed_genesis()

    def _seed_genesis(self) -> None:
        """Initializes deterministic genesis block if empty."""
        if not self._events:
            genesis = AuditEvent.create_genesis()
            self._events.append(genesis)
            logger.info(f"[AuditService] Seeded Genesis audit block: {genesis.entry_hash[:16]}...")

    @property
    def latest_event(self) -> AuditEvent:
        return self._events[-1]

    async def log_event(
        self,
        category: AuditCategory,
        actor: str,
        action: str,
        target_resource: str,
        outcome: AuditOutcome,
        session_id: str = "default",
        model_name: str | None = None,
        operator_approved: bool = False,
        trace_id: str | None = None,
        span_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Atomically appends, chains, and seals a new audit block."""
        async with self._chain_lock:
            prev_event = self._events[-1]
            next_seq = prev_event.sequence_num + 1

            event = AuditEvent(
                sequence_num=next_seq,
                category=category,
                actor=actor,
                action=action,
                target_resource=target_resource,
                outcome=outcome,
                session_id=session_id,
                model_name=model_name,
                operator_approved=operator_approved,
                trace_id=trace_id,
                span_id=span_id,
                prev_hash=prev_event.entry_hash,
                metadata=metadata or {},
                timestamp=time.time(),
            )
            event.seal()
            self._events.append(event)

            logger.debug(
                f"[AuditService] Appended block #{event.sequence_num} ({event.category.value}) "
                f"Hash: {event.entry_hash[:16]} (Prev: {event.prev_hash[:16]})"
            )
            return event

    def verify_integrity(self) -> VerificationResult:
        """Runs full chain verification over all logged events."""
        return AuditIntegrityVerifier.verify_chain(self._events)

    def get_events(self, limit: int = 100) -> list[dict[str, Any]]:
        return [e.to_dict() for e in self._events[-limit:]]


audit_service = AuditService()
