"""Central Policy Registry & Unified Governance Authority for C.O.P.P.E.R.

Consolidates and validates policy domains: Security, Agent Permissions, Network,
Model Routing, Safety, and Privacy under a single versioned runtime authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from app.core.logger import logger
from app.core.privacy.classification import DataClassification, get_governance_policy
from app.core.safety.policy_engine import safety_policy_engine


class PolicyDomain(str, Enum):
    SECURITY = "SECURITY"
    AGENT_PERMISSIONS = "AGENT_PERMISSIONS"
    NETWORK_EGRESS = "NETWORK_EGRESS"
    MODEL_ROUTING = "MODEL_ROUTING"
    SAFETY = "SAFETY"
    PRIVACY = "PRIVACY"


@dataclass
class RegisteredPolicy:
    policy_id: str
    domain: PolicyDomain
    name: str
    description: str
    version: str = "1.0.0"
    is_active: bool = True
    enforced_by: str = "runtime_kernel"
    rules: dict[str, Any] = field(default_factory=dict)


class CentralPolicyRegistry:
    """Authoritative registry for all COPPER platform governance policies."""

    def __init__(self):
        self._policies: dict[str, RegisteredPolicy] = {}
        self._init_default_policies()

    def _init_default_policies(self) -> None:
        # 1. Security Policy
        self.register_policy(
            RegisteredPolicy(
                policy_id="POL-SEC-01",
                domain=PolicyDomain.SECURITY,
                name="ZeroTrustLeastPrivilege",
                description="Enforce agent token capability checking and RBAC boundaries on all tool calls.",
                enforced_by="ToolAuthorizationPolicy",
                rules={"enforce_agent_tokens": True, "sandbox_untrusted_code": True},
            )
        )

        # 2. Network Egress Policy
        self.register_policy(
            RegisteredPolicy(
                policy_id="POL-NET-01",
                domain=PolicyDomain.NETWORK_EGRESS,
                name="LocalServicesNetworkPolicy",
                description="Restrict network calls to loopback services (Ollama, SearXNG, Redis). Block public WAN unless consented.",
                enforced_by="DataFirewall & SSRFValidator",
                rules={"mode": "user_authorized_egress", "allow_loopback": True},
            )
        )

        # 3. Privacy Policy
        self.register_policy(
            RegisteredPolicy(
                policy_id="POL-PRIV-01",
                domain=PolicyDomain.PRIVACY,
                name="FiveTierDataRetention",
                description="Enforce retention TTLs and verifiable cascading erasure across all 5 data stores.",
                enforced_by="DataGovernanceManager",
                rules={"classifications": [c.value for c in DataClassification]},
            )
        )

        # 4. Safety Policy
        self.register_policy(
            RegisteredPolicy(
                policy_id="POL-SAFE-01",
                domain=PolicyDomain.SAFETY,
                name="FourTierActionRiskGating",
                description="Classify actions into 4 tiers and mandate escalation tickets for consequential actions.",
                enforced_by="ActionSafetyClassifier & SafetyEscalationManager",
                rules={"irreversible_blocked": True, "consequential_requires_ticket": True},
            )
        )

    def register_policy(self, policy: RegisteredPolicy) -> None:
        self._policies[policy.policy_id] = policy
        logger.info(f"[CentralPolicyRegistry] Registered policy {policy.policy_id} ({policy.name}) in domain {policy.domain.value}")

    def get_policy(self, policy_id: str) -> RegisteredPolicy | None:
        return self._policies.get(policy_id)

    def get_policies_for_domain(self, domain: PolicyDomain) -> list[RegisteredPolicy]:
        return [p for p in self._policies.values() if p.domain == domain]

    def list_policies(self, domain: PolicyDomain | None = None) -> list[dict[str, Any]]:
        policies = list(self._policies.values())
        if domain:
            policies = [p for p in policies if p.domain == domain]
        return [asdict(p) for p in policies]


central_policy_registry = CentralPolicyRegistry()
