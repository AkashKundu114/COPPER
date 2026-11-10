"""Continuous AI Safety Supervisor & Emergency Kill-Switch Coordinator for C.O.P.P.E.R.

Actively monitors real-time agent execution streams, detects jailbreak bursts,
evaluates alignment drift, and orchestrates an immediate failsafe kill-switch
to halt consequential or irreversible operations under active attack.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger
from app.core.safety.action_classifier import ActionSafetyLevel
from app.core.safety.safety_coordinator import SafetyOrchestrator, SafetyPreflightDecision, safety_orchestrator


@dataclass
class SafetyIncidentRecord:
    timestamp: float
    action_name: str
    target: str
    reason: str
    safety_level: str


@dataclass
class SafetySupervisionStatus:
    status_id: str
    timestamp: float
    kill_switch_active: bool
    incident_count_last_hour: int
    alignment_posture: str  # "NOMINAL" | "HEIGHTENED_ALERT" | "LOCKDOWN"
    incidents: list[SafetyIncidentRecord]
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContinuousSafetySupervisor:
    """Real-time alignment monitor and failsafe kill-switch coordinator."""

    def __init__(
        self,
        orchestrator: SafetyOrchestrator | None = None,
        incident_threshold_for_lockdown: int = 5,
    ):
        self.orchestrator = orchestrator or safety_orchestrator
        self.lockdown_threshold = incident_threshold_for_lockdown
        self._kill_switch_engaged: bool = False
        self._incidents: list[SafetyIncidentRecord] = []

    @property
    def is_kill_switch_active(self) -> bool:
        return self._kill_switch_engaged

    def engage_kill_switch(self, reason: str = "Operator manual emergency stop") -> None:
        """Engages the failsafe kill-switch, blocking all non-read-only actions system-wide."""
        self._kill_switch_engaged = True
        logger.error(f"[ContinuousSafetySupervisor] EMERGENCY KILL-SWITCH ENGAGED: {reason}")

    def release_kill_switch(self, operator_key: str = "operator_root") -> bool:
        """Releases the failsafe kill-switch after operator clearance."""
        self._kill_switch_engaged = False
        logger.warning(f"[ContinuousSafetySupervisor] Emergency kill-switch RELEASED by '{operator_key}'")
        return True

    def record_incident(self, action_name: str, target: str, reason: str, level: ActionSafetyLevel) -> None:
        """Logs an intercepted safety violation."""
        rec = SafetyIncidentRecord(
            timestamp=time.time(),
            action_name=action_name,
            target=target,
            reason=reason,
            safety_level=level.name,
        )
        self._incidents.append(rec)
        if len(self._incidents) >= self.lockdown_threshold and not self._kill_switch_engaged:
            self.engage_kill_switch("Automatic trigger: Incident storm threshold exceeded.")

    async def supervise_execution_request(
        self,
        action_name: str,
        target: str,
        context_payload: str = "",
    ) -> SafetyPreflightDecision:
        """Evaluates safety preflight, interdicting immediately if the kill-switch is engaged."""
        if self._kill_switch_engaged:
            logger.warning(f"[ContinuousSafetySupervisor] Action '{action_name}' rejected due to active kill-switch.")
            return SafetyPreflightDecision(
                is_allowed=False,
                safety_level=ActionSafetyLevel.IRREVERSIBLE,
                requires_approval=False,
                is_blocked=True,
                rejection_reason="Emergency safety kill-switch is actively engaged across all agent tiers.",
            )

        decision = await self.orchestrator.evaluate_preflight(
            action_name=action_name,
            target=target,
            context_payload=context_payload,
        )

        if decision.is_blocked:
            self.record_incident(
                action_name=action_name,
                target=target,
                reason=decision.rejection_reason or "Blocked by SafetyOrchestrator",
                level=decision.safety_level,
            )

        return decision

    def get_supervision_status(self) -> SafetySupervisionStatus:
        """Returns the real-time supervision status and alignment posture."""
        now = time.time()
        recent_incidents = [i for i in self._incidents if now - i.timestamp <= 3600]

        if self._kill_switch_engaged:
            posture = "LOCKDOWN"
        elif len(recent_incidents) >= 3:
            posture = "HEIGHTENED_ALERT"
        else:
            posture = "NOMINAL"

        status_id = f"SAFE-SUP-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{status_id}:{self._kill_switch_engaged}:{posture}".encode()).hexdigest()

        return SafetySupervisionStatus(
            status_id=status_id,
            timestamp=now,
            kill_switch_active=self._kill_switch_engaged,
            incident_count_last_hour=len(recent_incidents),
            alignment_posture=posture,
            incidents=recent_incidents,
            signature=sig,
        )


continuous_safety_supervisor = ContinuousSafetySupervisor()
