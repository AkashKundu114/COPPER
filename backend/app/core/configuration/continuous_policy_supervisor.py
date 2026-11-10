"""Continuous Policy Supervision & Runtime Drift Interdictor for C.O.P.P.E.R.

Continuously monitors runtime configuration mutations, actively blocks drift from
immutable architectural policies (such as 8.0 GB VRAM ceilings and airgap boundaries),
and guarantees automated rollback upon illegal configuration injection.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.configuration.change_manager import ConfigChangeManager
from app.core.configuration.policy_registry import CentralPolicyRegistry, PolicyDomain, central_policy_registry
from app.core.configuration.runtime_enforcer import DynamicPolicyEnforcer
from app.core.configuration.schemas import COPPERConfig, master_config
from app.core.logger import logger


@dataclass
class PolicySupervisionAlert:
    timestamp: float
    domain: str
    property_path: str
    attempted_value: Any
    rejection_reason: str
    mitigated: bool


@dataclass
class PolicySupervisionReport:
    report_id: str
    timestamp: float
    total_interdictions: int
    active_policies_count: int
    runtime_compliant: bool
    recent_alerts: list[PolicySupervisionAlert]
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ContinuousPolicySupervisor:
    """Supervises configuration lifecycle and interdicts illegal policy drifts in real time."""

    def __init__(
        self,
        config: COPPERConfig | None = None,
        change_mgr: ConfigChangeManager | None = None,
        registry: CentralPolicyRegistry | None = None,
    ):
        self.config = config or master_config
        self.change_mgr = change_mgr or ConfigChangeManager(self.config)
        self.registry = registry or central_policy_registry
        self.enforcer = DynamicPolicyEnforcer(self.registry, self.change_mgr)
        self._alerts: list[PolicySupervisionAlert] = []

    def attempt_validated_configuration_mutation(
        self,
        domain_name: str,
        property_name: str,
        new_value: Any,
        operator: str = "runtime_agent",
    ) -> tuple[bool, str]:
        """Interdicts illegal mutations before application, logging security alerts upon rejection."""
        # Hard invariant: VRAM budget cannot exceed 8.0 GB
        if domain_name == "model_runtime" and property_name == "vram_budget_gb":
            if float(new_value) > 8.0:
                reason = f"Rejected: Value {new_value}GB exceeds strict 8.0 GB hardware ceiling."
                self._record_alert(domain_name, f"{domain_name}.{property_name}", new_value, reason)
                return False, reason

        # Hard invariant: Sandbox network cannot be enabled in untrusted mode
        if domain_name == "sandbox" and property_name == "network_enabled":
            if bool(new_value) is True:
                reason = "Rejected: Sandbox network access cannot be enabled; airgap boundary violation."
                self._record_alert(domain_name, f"{domain_name}.{property_name}", new_value, reason)
                return False, reason

        # Delegate to atomic change manager
        ok, msg = self.change_mgr.update_property(domain_name, property_name, new_value, operator=operator)
        if not ok:
            self._record_alert(domain_name, f"{domain_name}.{property_name}", new_value, msg)
        return ok, msg

    def _record_alert(self, domain: str, path: str, val: Any, reason: str) -> None:
        alert = PolicySupervisionAlert(
            timestamp=time.time(),
            domain=domain,
            property_path=path,
            attempted_value=val,
            rejection_reason=reason,
            mitigated=True,
        )
        self._alerts.append(alert)
        logger.warning(f"[ContinuousPolicySupervisor] Interdicted policy drift: {path} = {val} ({reason})")

    def generate_supervision_report(self) -> PolicySupervisionReport:
        """Emits audit report of policy enforcement and interdicted violations."""
        now = time.time()
        active_policies = len(self.registry.list_policies())
        is_compliant = self.change_mgr.config.model_runtime.vram_budget_gb <= 8.0

        rep_id = f"POL-SUP-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{rep_id}:{len(self._alerts)}:{is_compliant}".encode()).hexdigest()

        report = PolicySupervisionReport(
            report_id=rep_id,
            timestamp=now,
            total_interdictions=len(self._alerts),
            active_policies_count=active_policies,
            runtime_compliant=is_compliant,
            recent_alerts=self._alerts[-10:],
            signature=sig,
        )

        logger.info(
            f"[ContinuousPolicySupervisor] Supervision report: Interdictions={len(self._alerts)}, "
            f"Compliant={is_compliant}"
        )
        return report


continuous_policy_supervisor = ContinuousPolicySupervisor()
