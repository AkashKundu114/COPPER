"""Real-Time Operator Approval Channel for C.O.P.P.E.R.

Provides asynchronous, human-in-the-loop confirmation for consequential (Level 2)
and safety-gated operations via WebSocket broadcast and REST response channels.
"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

from app.core.logger import logger


class TicketStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class ApprovalTicket:
    ticket_id: str
    action: str
    target: str
    actor: str
    reason: str
    required_controls: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 60.0)
    status: TicketStatus = TicketStatus.PENDING
    decision_reason: Optional[str] = None
    confirmed_by: Optional[str] = None

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class OperatorApprovalManager:
    """Manages real-time operator approval tickets and WebSocket notifications."""

    def __init__(self, default_timeout_sec: float = 60.0):
        self.default_timeout_sec = default_timeout_sec
        self._tickets: dict[str, ApprovalTicket] = {}
        self._futures: dict[str, asyncio.Future[bool]] = {}
        self._broadcast_hooks: list[Callable[[dict[str, Any]], Coroutine[Any, Any, None]]] = []

    def register_broadcast_hook(self, hook: Callable[[dict[str, Any]], Coroutine[Any, Any, None]]) -> None:
        """Registers a callback (e.g. WebSocket manager) to push approval events to UI."""
        self._broadcast_hooks.append(hook)

    async def create_ticket(
        self,
        action: str,
        target: str,
        actor: str,
        reason: str,
        required_controls: Optional[list[str]] = None,
        timeout_seconds: Optional[float] = None,
    ) -> ApprovalTicket:
        """Creates an approval ticket and broadcasts it to connected operator clients."""
        timeout = timeout_seconds or self.default_timeout_sec
        now = time.time()
        ticket_id = f"appr_{uuid.uuid4().hex[:12]}"

        ticket = ApprovalTicket(
            ticket_id=ticket_id,
            action=action,
            target=target,
            actor=actor,
            reason=reason,
            required_controls=required_controls or [],
            created_at=now,
            expires_at=now + timeout,
            status=TicketStatus.PENDING,
        )

        self._tickets[ticket_id] = ticket
        loop = asyncio.get_running_loop()
        self._futures[ticket_id] = loop.create_future()

        # Broadcast event to UI
        event = {
            "type": "operator_approval_request",
            "ticket": ticket.to_dict(),
            "timestamp": now,
        }
        for hook in self._broadcast_hooks:
            try:
                await hook(event)
            except Exception as e:
                logger.debug(f"[ApprovalManager] Broadcast hook error: {e}")

        logger.info(f"[ApprovalManager] Created ticket {ticket_id} for '{action}' on '{target}' (Expires in {timeout}s)")
        return ticket

    async def wait_for_decision(self, ticket_id: str, timeout_seconds: Optional[float] = None) -> bool:
        """Asynchronously awaits human operator approval decision."""
        if ticket_id not in self._tickets or ticket_id not in self._futures:
            raise KeyError(f"Ticket '{ticket_id}' not found.")

        ticket = self._tickets[ticket_id]
        future = self._futures[ticket_id]
        timeout = timeout_seconds or max(1.0, ticket.expires_at - time.time())

        try:
            approved = await asyncio.wait_for(future, timeout=timeout)
            return approved
        except asyncio.TimeoutError:
            ticket.status = TicketStatus.EXPIRED
            ticket.decision_reason = "Operator approval request timed out."
            logger.warning(f"[ApprovalManager] Ticket {ticket_id} expired without decision.")
            return False
        finally:
            self._futures.pop(ticket_id, None)

    def resolve_ticket(
        self,
        ticket_id: str,
        approved: bool,
        reason: str = "",
        confirmed_by: str = "operator",
    ) -> bool:
        """Records human operator decision and resumes waiting tasks."""
        if ticket_id not in self._tickets:
            logger.warning(f"[ApprovalManager] Attempted to resolve unknown ticket '{ticket_id}'")
            return False

        ticket = self._tickets[ticket_id]
        if ticket.status != TicketStatus.PENDING:
            logger.warning(f"[ApprovalManager] Ticket '{ticket_id}' is already {ticket.status.value}")
            return False

        ticket.status = TicketStatus.APPROVED if approved else TicketStatus.REJECTED
        ticket.decision_reason = reason or ("Approved by operator" if approved else "Rejected by operator")
        ticket.confirmed_by = confirmed_by

        fut = self._futures.get(ticket_id)
        if fut and not fut.done():
            fut.set_result(approved)

        logger.info(f"[ApprovalManager] Ticket {ticket_id} resolved: {ticket.status.value} by {confirmed_by}")
        return True

    def get_pending_tickets(self) -> list[dict[str, Any]]:
        """Returns all currently active pending approval tickets."""
        now = time.time()
        active = []
        for t in list(self._tickets.values()):
            if t.status == TicketStatus.PENDING:
                if t.is_expired():
                    t.status = TicketStatus.EXPIRED
                else:
                    active.append(t.to_dict())
        return active

    def get_ticket(self, ticket_id: str) -> Optional[dict[str, Any]]:
        ticket = self._tickets.get(ticket_id)
        return ticket.to_dict() if ticket else None


# Global Operator Approval Manager Singleton
operator_approval_manager = OperatorApprovalManager()
