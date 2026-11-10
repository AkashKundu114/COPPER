"""Unified Safety Orchestrator & Multi-Tier Alignment Coordinator for C.O.P.P.E.R.

Integrates action risk gating, prompt injection quarantine, epistemic claim classification,
and human-in-the-loop escalation into a single atomic safety enforcement pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.logger import logger
from app.core.safety.action_classifier import (
    ActionClassification,
    ActionSafetyClassifier,
    ActionSafetyLevel,
    action_safety_classifier,
)
from app.core.safety.escalation import (
    EscalationTicket,
    SafetyEscalationManager,
    TicketStatus,
    safety_escalation_manager,
)
from app.core.safety.information_safety import EpistemicClaim, EpistemicStatus, InformationSafetyGuard


@dataclass
class SafetyPreflightDecision:
    is_allowed: bool
    safety_level: ActionSafetyLevel
    requires_approval: bool
    is_blocked: bool = False
    quarantined_context: str | None = None
    quarantined_injections_count: int = 0
    challenge: EscalationTicket | None = None
    epistemic_claims: list[EpistemicClaim] = field(default_factory=list)
    rejection_reason: str | None = None


class SafetyOrchestrator:
    """Atomic orchestrator for pre-execution safety gating, input sanitization, and escalation."""

    def __init__(
        self,
        classifier: ActionSafetyClassifier = action_safety_classifier,
        escalator: SafetyEscalationManager = safety_escalation_manager,
        info_guard: InformationSafetyGuard | None = None,
    ):
        self.classifier = classifier
        self.escalator = escalator
        self.info_guard = info_guard or InformationSafetyGuard(uncertainty_threshold=0.60)

    async def evaluate_preflight(
        self,
        action_name: str,
        target: str,
        context_payload: str = "",
        operator_token: str | None = None,
        confidence_score: float = 0.85,
    ) -> SafetyPreflightDecision:
        """Evaluates whether an action is safe to proceed, requires escalation, or must be blocked."""
        # 1. Neutralize any indirect prompt injection in retrieved context
        cleaned_context, quarantined = self.info_guard.sanitize_retrieved_context(context_payload)
        
        # 2. Epistemic claim classification
        claim = self.info_guard.classify_epistemic_claim(
            claim_text=f"Execute {action_name} on {target}",
            provenance="agent_plan",
            confidence=confidence_score,
        )

        # 3. Action Risk Classification
        classification = self.classifier.classify_tool_call(
            tool_name=action_name,
            arguments={"target": target},
        )
        level = classification.level

        # 4. Invariant hard block
        if classification.is_blocked or level == ActionSafetyLevel.IRREVERSIBLE:
            logger.warning(f"[SafetyOrchestrator] Hard blocked irreversible action: {action_name}")
            return SafetyPreflightDecision(
                is_allowed=False,
                safety_level=level,
                requires_approval=False,
                is_blocked=True,
                quarantined_context=cleaned_context,
                quarantined_injections_count=len(quarantined),
                epistemic_claims=[claim],
                rejection_reason=classification.reason,
            )

        # 5. Read-only or Reversible safe path
        if level in (ActionSafetyLevel.READ_ONLY, ActionSafetyLevel.REVERSIBLE):
            return SafetyPreflightDecision(
                is_allowed=True,
                safety_level=level,
                requires_approval=False,
                quarantined_context=cleaned_context,
                quarantined_injections_count=len(quarantined),
                epistemic_claims=[claim],
            )

        # 6. Consequential operations require approval ticket
        if operator_token:
            ticket = self.escalator.get_ticket(operator_token)
            if ticket and ticket.is_valid_approval():
                logger.info(f"[SafetyOrchestrator] Escalated approval ticket verified for {action_name}")
                return SafetyPreflightDecision(
                    is_allowed=True,
                    safety_level=level,
                    requires_approval=True,
                    quarantined_context=cleaned_context,
                    quarantined_injections_count=len(quarantined),
                    epistemic_claims=[claim],
                )
            else:
                return SafetyPreflightDecision(
                    is_allowed=False,
                    safety_level=level,
                    requires_approval=True,
                    quarantined_context=cleaned_context,
                    quarantined_injections_count=len(quarantined),
                    rejection_reason="Invalid or expired operator approval ticket",
                )

        # Ticket not provided: Create escalation ticket
        ticket = self.escalator.create_ticket(
            target_tool=action_name,
            action_repr=f"{action_name}(target={target})",
            reason=classification.reason,
        )
        logger.warning(f"[SafetyOrchestrator] Action '{action_name}' challenged. Issued ticket: {ticket.ticket_id}")

        return SafetyPreflightDecision(
            is_allowed=False,
            safety_level=level,
            requires_approval=True,
            quarantined_context=cleaned_context,
            quarantined_injections_count=len(quarantined),
            challenge=ticket,
            epistemic_claims=[claim],
            rejection_reason=f"Action requires explicit operator approval [Ticket {ticket.ticket_id}]",
        )


safety_orchestrator = SafetyOrchestrator()
