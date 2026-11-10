"""Human Escalation & Operator Approval Ticket Manager for C.O.P.P.E.R.

Provides verifiable human-in-the-loop approval workflows for consequential
agent operations, enforcing approval tickets with cryptographic IDs and TTLs.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from app.core.logger import logger


class TicketStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class EscalationTicket:
    action_repr: str
    reason: str
    target_tool: str
    ticket_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TicketStatus = TicketStatus.PENDING
    created_at: float = field(default_factory=time.time)
    expires_at: float = field(default_factory=lambda: time.time() + 300.0)  # 5 minute TTL
    operator_notes: str | None = None
    context: dict[str, Any] = field(default_factory=dict)

    def is_valid_approval(self) -> bool:
        if self.status != TicketStatus.APPROVED:
            return False
        if time.time() > self.expires_at:
            self.status = TicketStatus.EXPIRED
            return False
        return True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data


class SafetyEscalationManager:
    """Manages creation, review, and resolution of operator escalation tickets."""

    def __init__(self, default_ttl_seconds: float = 300.0):
        self.default_ttl = default_ttl_seconds
        self._tickets: dict[str, EscalationTicket] = {}

    def create_ticket(
        self,
        target_tool: str,
        action_repr: str,
        reason: str,
        context: dict[str, Any] | None = None,
    ) -> EscalationTicket:
        now = time.time()
        ticket = EscalationTicket(
            target_tool=target_tool,
            action_repr=action_repr,
            reason=reason,
            created_at=now,
            expires_at=now + self.default_ttl,
            context=context or {},
        )
        self._tickets[ticket.ticket_id] = ticket
        logger.warning(
            f"[EscalationManager] Created approval ticket {ticket.ticket_id} for tool '{target_tool}': {reason}"
        )
        return ticket

    def approve_ticket(self, ticket_id: str, operator_notes: str = "") -> bool:
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return False
        if time.time() > ticket.expires_at:
            ticket.status = TicketStatus.EXPIRED
            return False

        ticket.status = TicketStatus.APPROVED
        ticket.operator_notes = operator_notes
        logger.info(f"[EscalationManager] Ticket {ticket_id} APPROVED by operator.")
        return True

    def reject_ticket(self, ticket_id: str, operator_notes: str = "") -> bool:
        ticket = self._tickets.get(ticket_id)
        if not ticket:
            return False
        ticket.status = TicketStatus.REJECTED
        ticket.operator_notes = operator_notes
        logger.info(f"[EscalationManager] Ticket {ticket_id} REJECTED by operator.")
        return True

    def get_ticket(self, ticket_id: str) -> EscalationTicket | None:
        ticket = self._tickets.get(ticket_id)
        if ticket and ticket.status == TicketStatus.PENDING and time.time() > ticket.expires_at:
            ticket.status = TicketStatus.EXPIRED
        return ticket


safety_escalation_manager = SafetyEscalationManager()
