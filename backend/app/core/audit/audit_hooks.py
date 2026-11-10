"""Runtime Audit Event Interceptors & Auto-Instrumentation Hooks for C.O.P.P.E.R.

Captures tool execution events, safety interventions, and memory mutations,
sanitizing credentials/PII and appending cryptographically chained records to the AuditService.
"""

from __future__ import annotations

from typing import Any

from app.core.audit.audit_event import AuditCategory, AuditEvent, AuditOutcome
from app.core.audit.audit_service import audit_service
from app.core.data_firewall import redact
from app.core.logger import logger


class AuditHookInterceptor:
    """Interceps runtime system events and logs verifiable audit blocks."""

    def __init__(self, service=audit_service):
        self.service = service

    async def on_tool_executed(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        success: bool,
        actor: str = "agent",
        model_name: str | None = None,
        operator_approved: bool = False,
        trace_id: str | None = None,
        execution_time_ms: float = 0.0,
    ) -> AuditEvent:
        """Records an auditable tool execution event."""
        # Sanitize arguments of sensitive PII or credentials before persisting in audit
        raw_args_repr = str(arguments)
        sanitized_summary = redact(f"{tool_name}({raw_args_repr[:120]}...)")

        outcome = AuditOutcome.SUCCESS if success else AuditOutcome.FAILED
        event = await self.service.log_event(
            category=AuditCategory.TOOL_EXECUTED,
            actor=actor,
            action=f"execute_tool:{tool_name}",
            target_resource=f"tool:{tool_name}",
            outcome=outcome,
            model_name=model_name,
            operator_approved=operator_approved,
            trace_id=trace_id,
            metadata={
                "tool_name": tool_name,
                "sanitized_summary": sanitized_summary,
                "execution_time_ms": execution_time_ms,
            },
        )
        return event

    async def on_guardian_intervention(
        self,
        action_repr: str,
        verdict_level: str,
        reasoning: str,
        actor: str = "guardian_engine",
        blocked: bool = False,
    ) -> AuditEvent:
        """Records a safety intervention or challenge event."""
        cat = AuditCategory.GUARDIAN_SAFETY_BLOCK if blocked else AuditCategory.GUARDIAN_CHALLENGE
        outcome = AuditOutcome.BLOCKED if blocked else AuditOutcome.CHALLENGED

        event = await self.service.log_event(
            category=cat,
            actor=actor,
            action=f"guardian_intervention:{verdict_level}",
            target_resource="safety_gate",
            outcome=outcome,
            metadata={
                "action_repr": action_repr[:100],
                "verdict_level": verdict_level,
                "reasoning": reasoning[:200],
            },
        )
        return event


audit_hook_interceptor = AuditHookInterceptor()
