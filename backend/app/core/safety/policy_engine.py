"""Centralized, Versioned Safety Policy Engine for C.O.P.P.E.R.

Enforces model-agnostic safety policies, permission boundaries, and
semantic conflict resolution across all agents, models, and workflows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import IntEnum
from typing import Any

from app.core.logger import logger


class PolicyLevel(IntEnum):
    """Hierarchical policy authority tiers. Higher numerical value takes precedence."""
    AGENT_HEURISTIC = 40
    SECURITY_BASELINE = 60
    OPERATOR_DIRECTIVE = 80
    SYSTEM_INVARIANT = 100


@dataclass(frozen=True)
class PolicyVersion:
    major: int
    minor: int
    patch: int
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def __str__(self) -> str:
        return f"v{self.major}.{self.minor}.{self.patch}"


@dataclass
class SafetyRule:
    rule_id: str
    name: str
    description: str
    level: PolicyLevel
    action_type: str  # e.g., "tool_execution", "system_prompt", "network_egress", "file_system"
    condition: str
    is_blocked: bool = True
    requires_confirmation: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


class SafetyPolicyEngine:
    """Centralized authority for AI safety, invariant enforcement, and conflict resolution."""

    def __init__(self, version: PolicyVersion | None = None):
        self.version = version or PolicyVersion(1, 0, 0)
        self._rules: dict[str, SafetyRule] = {}
        self._init_core_invariants()

    def _init_core_invariants(self) -> None:
        """Initializes core, immutable system invariants that cannot be overridden."""
        invariants = [
            SafetyRule(
                rule_id="INV-001",
                name="PreventHostDriveWiping",
                description="Unconditionally forbid wiping system root or format volume commands.",
                level=PolicyLevel.SYSTEM_INVARIANT,
                action_type="file_system",
                condition="format | rm -rf / | clear-disk | wipe partitions",
                is_blocked=True,
                requires_confirmation=False,
            ),
            SafetyRule(
                rule_id="INV-002",
                name="CredentialExtractionInterdiction",
                description="Forbid extracting, dumping, or transmitting unencrypted system credentials or passwords.",
                level=PolicyLevel.SYSTEM_INVARIANT,
                action_type="credential_access",
                condition="dump sam | mimikatz | extract passwords | steal credentials",
                is_blocked=True,
                requires_confirmation=False,
            ),
            SafetyRule(
                rule_id="INV-003",
                name="AntiSelfModification",
                description="Prevent autonomous modification or deletion of core safety policies or guardian code.",
                level=PolicyLevel.SYSTEM_INVARIANT,
                action_type="self_modification",
                condition="modify_safety_policy | override_guardian | patch_firewall",
                is_blocked=True,
                requires_confirmation=False,
            ),
            SafetyRule(
                rule_id="SEC-001",
                name="ConsequentialDiskModificationConfirmation",
                description="Require operator confirmation for consequential write or delete operations.",
                level=PolicyLevel.SECURITY_BASELINE,
                action_type="file_system",
                condition="delete_file | overwrite_database | drop_table",
                is_blocked=False,
                requires_confirmation=True,
            ),
        ]
        for inv in invariants:
            self._rules[inv.rule_id] = inv

    def register_rule(self, rule: SafetyRule) -> tuple[bool, str]:
        """Registers a safety rule, enforcing conflict resolution and priority hierarchy."""
        if rule.rule_id in self._rules:
            existing = self._rules[rule.rule_id]
            if existing.level == PolicyLevel.SYSTEM_INVARIANT and rule.level < PolicyLevel.SYSTEM_INVARIANT:
                msg = f"Cannot override System Invariant '{rule.rule_id}' with lower priority level {rule.level.name}."
                logger.warning(f"[SafetyPolicyEngine] {msg}")
                return False, msg

            if rule.level < existing.level:
                msg = f"Rule registration rejected: existing rule '{rule.rule_id}' has higher authority ({existing.level.name} > {rule.level.name})."
                logger.warning(f"[SafetyPolicyEngine] {msg}")
                return False, msg

        self._rules[rule.rule_id] = rule
        logger.info(f"[SafetyPolicyEngine] Registered rule '{rule.rule_id}' ({rule.name}) at level {rule.level.name}.")
        return True, "Rule successfully registered"

    def evaluate_action(self, action_type: str, action_content: str) -> tuple[bool, bool, str | None]:
        """Evaluates proposed action against active policies.
        
        Returns:
            (is_permitted, requires_confirmation, reason)
        """
        content_lower = action_content.lower()

        # Check all matching rules ordered by descending authority level
        matched_rules: list[SafetyRule] = []
        for rule in self._rules.values():
            if rule.action_type == action_type or rule.action_type == "*":
                # Keyword condition check
                triggers = [t.strip() for t in rule.condition.split("|")]
                if any(t in content_lower for t in triggers if t):
                    matched_rules.append(rule)

        if not matched_rules:
            return True, False, None

        # Sort by level descending (highest priority rule determines outcome)
        matched_rules.sort(key=lambda r: int(r.level), reverse=True)
        dominant_rule = matched_rules[0]

        if dominant_rule.is_blocked:
            return False, dominant_rule.requires_confirmation, f"Blocked by {dominant_rule.level.name} [{dominant_rule.rule_id}]: {dominant_rule.description}"

        if dominant_rule.requires_confirmation:
            return True, True, f"Operator confirmation required by {dominant_rule.level.name} [{dominant_rule.rule_id}]: {dominant_rule.description}"

        return True, False, None

    def list_rules(self) -> list[dict[str, Any]]:
        return [
            {
                "rule_id": r.rule_id,
                "name": r.name,
                "description": r.description,
                "level": r.level.name,
                "level_value": int(r.level),
                "action_type": r.action_type,
                "is_blocked": r.is_blocked,
                "requires_confirmation": r.requires_confirmation,
            }
            for r in self._rules.values()
        ]


safety_policy_engine = SafetyPolicyEngine()
