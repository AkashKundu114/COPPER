"""Dynamic Policy Enforcement Engine & Hot-Reload Supervisor for C.O.P.P.E.R.

Integrates CentralPolicyRegistry and ChangeManager, providing live policy evaluation,
hot-reloading of configuration with validation gates, and automated rollback upon violations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.configuration.change_manager import (
    ConfigChangeAuditRecord,
    ConfigChangeManager,
    config_change_manager,
)
from app.core.configuration.policy_registry import (
    CentralPolicyRegistry,
    PolicyDomain,
    RegisteredPolicy,
    central_policy_registry,
)
from app.core.logger import logger


@dataclass
class PolicyEvaluationResult:
    allowed: bool
    domain: PolicyDomain
    policy_id: str
    rejection_reason: str | None = None
    parameters_checked: dict[str, Any] = field(default_factory=dict)


class DynamicPolicyEnforcer:
    """Enforces active policies in real time and supervises configuration reload safety."""

    def __init__(
        self,
        registry: CentralPolicyRegistry = central_policy_registry,
        cm: ConfigChangeManager = config_change_manager,
    ):
        self.registry = registry
        self.change_manager = cm

    def evaluate_operation(
        self,
        domain: PolicyDomain,
        operation_context: dict[str, Any],
    ) -> PolicyEvaluationResult:
        """Evaluates whether an operation satisfies all active policies within a domain."""
        policies = self.registry.get_policies_for_domain(domain)
        
        for pol in policies:
            if not pol.is_active:
                continue

            # Check network egress policies
            if domain == PolicyDomain.NETWORK_EGRESS:
                target_ip = operation_context.get("destination_ip", "")
                is_local = target_ip in ("127.0.0.1", "localhost", "::1")
                if not is_local and pol.rules.get("allow_external") is False:
                    reason = f"Policy violation [{pol.policy_id}]: Unauthorized external egress to {target_ip}"
                    logger.warning(f"[DynamicPolicyEnforcer] {reason}")
                    return PolicyEvaluationResult(
                        allowed=False,
                        domain=domain,
                        policy_id=pol.policy_id,
                        rejection_reason=reason,
                        parameters_checked={"destination_ip": target_ip},
                    )

            # Check model routing VRAM policies
            if domain == PolicyDomain.MODEL_ROUTING:
                est_vram = operation_context.get("estimated_vram_gb", 0.0)
                max_allowed = pol.rules.get("max_vram_gb", 8.0)
                if est_vram > max_allowed:
                    reason = f"Policy violation [{pol.policy_id}]: Model VRAM {est_vram}GB exceeds ceiling {max_allowed}GB"
                    logger.warning(f"[DynamicPolicyEnforcer] {reason}")
                    return PolicyEvaluationResult(
                        allowed=False,
                        domain=domain,
                        policy_id=pol.policy_id,
                        rejection_reason=reason,
                        parameters_checked={"estimated_vram_gb": est_vram, "limit": max_allowed},
                    )

            # Check security least privilege
            if domain == PolicyDomain.SECURITY:
                role = operation_context.get("role", "guest")
                action = operation_context.get("action", "")
                blocked_actions = pol.rules.get("blocked_for_guest", ["delete", "drop", "purge"])
                if role == "guest" and action in blocked_actions:
                    reason = f"Policy violation [{pol.policy_id}]: Role 'guest' cannot perform action '{action}'"
                    return PolicyEvaluationResult(
                        allowed=False,
                        domain=domain,
                        policy_id=pol.policy_id,
                        rejection_reason=reason,
                        parameters_checked={"role": role, "action": action},
                    )

        return PolicyEvaluationResult(
            allowed=True,
            domain=domain,
            policy_id="ALL_POLICIES_SATISFIED",
            parameters_checked=operation_context,
        )

    def apply_validated_config_update(
        self,
        domain_name: str,
        property_name: str,
        new_value: Any,
        modified_by: str = "operator",
    ) -> tuple[bool, str]:
        """Atomically applies a configuration change with schema verification and rollback protection."""
        # 1. Reject invalid VRAM allocations above 8.0 GB
        if property_name in ("max_vram_gb", "vram_budget_gb") and isinstance(new_value, (int, float)) and new_value > 8.0:
            return False, "Validation rejected: VRAM ceiling cannot exceed 8.0 GB hard limit"

        return self.change_manager.update_property(
            domain=domain_name,
            property_name=property_name,
            new_value=new_value,
            operator=modified_by,
        )


dynamic_policy_enforcer = DynamicPolicyEnforcer()
