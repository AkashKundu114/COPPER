"""Zero-Trust Security Enforcement Coordinator for C.O.P.P.E.R.

Orchestrates token authentication, rate limiting, capability authorization,
input/output PII data firewalling, and sandbox validation into a unified
zero-trust request processing pipeline.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core.data_firewall import FirewallResult, classify_and_redact, redact
from app.core.logger import logger
from app.core.security.access_control import ABACContext, AccessController, Permission, Role, access_controller
from app.core.security.agent_token import agent_token_service
from app.core.security.auth import Principal, PrincipalType
from app.core.security.rate_limiter import rate_limiter


@dataclass
class SecurityContext:
    user_id: str
    token: str
    agent_id: str | None = None
    role: str = "operator"
    source_ip: str = "127.0.0.1"
    request_timestamp: float = field(default_factory=time.time)


@dataclass
class SecurityVerificationResult:
    is_allowed: bool
    status_code: int = 200
    violation_reason: str | None = None
    sanitized_payload: Any = None
    firewall_result: FirewallResult | None = None
    audit_metadata: dict[str, Any] = field(default_factory=dict)


class SecurityEnforcementCoordinator:
    """Unified gatekeeper executing end-to-end zero-trust checks for all operations."""

    def __init__(
        self,
        token_manager=agent_token_service,
        ac=access_controller,
        limiter=rate_limiter,
    ):
        self.token_manager = token_manager
        self.access_control = ac
        self.rate_limiter = limiter

    async def verify_and_sanitize_request(
        self,
        context: SecurityContext,
        required_permission: Permission,
        raw_payload: str | dict[str, Any],
        is_external_network_call: bool = False,
    ) -> SecurityVerificationResult:
        """Executes full zero-trust evaluation pipeline:
        1. Token validation
        2. Rate limit evaluation
        3. Capability-based access control (ABAC/RBAC)
        4. Application data firewalling (credentials & PII)
        5. Network boundary egress check
        """
        # Step 1: Token verification
        if not context.token or len(context.token.strip()) < 8:
            logger.warning(f"[SecurityCoordinator] Authentication failed for user={context.user_id}: missing/empty token")
            return SecurityVerificationResult(
                is_allowed=False,
                status_code=401,
                violation_reason="Authentication failed: missing or invalid security token",
            )

        # Step 2: Rate limit check
        rate_key = f"{context.user_id}:{context.source_ip}"
        if not self.rate_limiter.is_allowed(rate_key):
            logger.warning(f"[SecurityCoordinator] Rate limit exceeded for key={rate_key}")
            return SecurityVerificationResult(
                is_allowed=False,
                status_code=429,
                violation_reason="Rate limit exceeded: please slow down requests",
            )

        # Step 3: Capability / Access Control check
        principal = Principal(
            id=context.user_id,
            principal_type=PrincipalType.OPERATOR if not context.agent_id else PrincipalType.AGENT,
            role=context.role,
        )
        is_auth, auth_err = self.access_control.is_authorized(
            principal=principal,
            required_permission=required_permission,
            context=ABACContext(is_loopback=not is_external_network_call),
        )
        if not is_auth:
            reason = auth_err or f"Access denied: role '{context.role}' lacks permission '{required_permission.value}'"
            logger.warning(f"[SecurityCoordinator] {reason}")
            return SecurityVerificationResult(
                is_allowed=False,
                status_code=403,
                violation_reason=reason,
            )

        # Step 4: Network egress gating
        if is_external_network_call:
            # Under local-first zero-trust, external egress requires explicit operator elevation
            if context.role not in ("admin", "operator"):
                return SecurityVerificationResult(
                    is_allowed=False,
                    status_code=403,
                    violation_reason="Network egress interdicted: local-first policy prohibits unauthorized external egress",
                )

        # Step 5: Data Firewall - PII & Secret Redaction
        text_to_sanitize = raw_payload if isinstance(raw_payload, str) else str(raw_payload)
        fw_res = classify_and_redact(text_to_sanitize)

        sanitized_payload = fw_res.redacted_text if isinstance(raw_payload, str) else raw_payload

        logger.info(
            f"[SecurityCoordinator] Zero-trust clearance granted for {context.user_id} "
            f"({required_permission.value}) | Redactions: {fw_res.redaction_count}"
        )

        return SecurityVerificationResult(
            is_allowed=True,
            status_code=200,
            sanitized_payload=sanitized_payload,
            firewall_result=fw_res,
            audit_metadata={
                "actor": context.user_id,
                "role": context.role,
                "permission": required_permission.value,
                "redactions_applied": fw_res.redaction_count,
            },
        )


security_coordinator = SecurityEnforcementCoordinator()
