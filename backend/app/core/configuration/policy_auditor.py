"""Central Configuration & Policy Compliance Auditor for C.O.P.P.E.R.

Audits running configurations against immutable architectural invariants:
strict 8.0 GB VRAM hardware ceilings, sandbox network airgaps, WAL mode persistence,
absence of plaintext credentials in config keys, and rollback readiness.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.configuration.change_manager import ConfigChangeManager
from app.core.configuration.policy_registry import CentralPolicyRegistry, central_policy_registry
from app.core.configuration.schemas import COPPERConfig, master_config
from app.core.logger import logger


@dataclass
class ConfigAuditCheck:
    check_id: str
    target: str
    passed: bool
    current_value: Any
    expected_rule: str
    remediation: str | None = None


@dataclass
class ConfigAuditReport:
    audit_id: str
    timestamp: float
    all_passed: bool
    passed_count: int
    total_checks: int
    checks: list[ConfigAuditCheck]
    rollback_verified: bool
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PolicyAuditor:
    """Audits COPPER runtime settings and active policies for architectural drift."""

    def __init__(
        self,
        config: COPPERConfig | None = None,
        change_mgr: ConfigChangeManager | None = None,
        policy_registry: CentralPolicyRegistry | None = None,
    ):
        self.config = config or master_config
        self.change_mgr = change_mgr or ConfigChangeManager(self.config)
        self.policy_registry = policy_registry or central_policy_registry

    def audit_vram_budget(self) -> ConfigAuditCheck:
        """Verifies VRAM allocation does not exceed host 8.0 GB hardware budget."""
        vram = self.config.model_runtime.vram_budget_gb
        passed = vram <= 8.0
        return ConfigAuditCheck(
            check_id="CFG-VRAM-CEILING",
            target="model_runtime.vram_budget_gb",
            passed=passed,
            current_value=vram,
            expected_rule="vram_budget_gb <= 8.0 GB",
            remediation=None if passed else "Lower vram_budget_gb to 8.0 GB or below.",
        )

    def audit_sandbox_isolation(self) -> ConfigAuditCheck:
        """Verifies untrusted code execution sandbox has strict network isolation."""
        net = self.config.sandbox.network_enabled
        passed = not net
        return ConfigAuditCheck(
            check_id="CFG-SANDBOX-AIRGAP",
            target="sandbox.network_enabled",
            passed=passed,
            current_value=net,
            expected_rule="sandbox.network_enabled == False (airgapped)",
            remediation=None if passed else "Set sandbox.network_enabled to False.",
        )

    def audit_database_durability(self) -> ConfigAuditCheck:
        """Verifies database is configured with WAL mode for zero data loss."""
        wal = self.config.database.enable_wal_mode
        return ConfigAuditCheck(
            check_id="CFG-DB-WAL-MODE",
            target="database.enable_wal_mode",
            passed=wal,
            current_value=wal,
            expected_rule="database.enable_wal_mode == True",
            remediation=None if wal else "Enable WAL journal mode on database connection.",
        )

    def audit_credential_exposure(self) -> ConfigAuditCheck:
        """Verifies that no API keys or secrets are stored in cleartext in configuration."""
        sensitive_keywords = ["sk-ant", "sk-", "password", "secret_key"]
        exposed: list[str] = []

        cfg_dict = self.config.model_dump()
        for domain, props in cfg_dict.items():
            if isinstance(props, dict):
                for k, v in props.items():
                    val_str = str(v).lower()
                    if any(kw in val_str for kw in sensitive_keywords):
                        exposed.append(f"{domain}.{k}")

        passed = len(exposed) == 0
        return ConfigAuditCheck(
            check_id="CFG-SECRETS-HYGIENE",
            target="master_config_secrets",
            passed=passed,
            current_value=exposed if exposed else "clean",
            expected_rule="Zero plaintext credentials in application config",
            remediation=None if passed else f"Move credentials to secure secret vault: {exposed}",
        )

    def verify_rollback_mechanism(self) -> bool:
        """Verifies that configuration change mutations can be rolled back safely."""
        initial_val = self.config.model_runtime.gatekeeper_model
        test_val = "test-rollback-probe:1.5b"

        # Apply update
        ok_update, _ = self.change_mgr.update_property(
            "model_runtime", "gatekeeper_model", test_val, operator="audit_prober"
        )
        if not ok_update:
            return False

        # Rollback
        ok_rollback, _ = self.change_mgr.rollback()
        restored_val = self.change_mgr.config.model_runtime.gatekeeper_model

        return ok_rollback and (restored_val == initial_val)

    def run_audit(self) -> ConfigAuditReport:
        """Executes complete policy and configuration audit."""
        checks = [
            self.audit_vram_budget(),
            self.audit_sandbox_isolation(),
            self.audit_database_durability(),
            self.audit_credential_exposure(),
        ]

        rollback_ok = self.verify_rollback_mechanism()
        passed_count = sum(1 for c in checks if c.passed)
        all_passed = (passed_count == len(checks)) and rollback_ok

        ts = time.time()
        audit_id = f"CFG-AUDIT-{hashlib.sha256(str(ts).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{audit_id}:{all_passed}:{passed_count}".encode()).hexdigest()

        report = ConfigAuditReport(
            audit_id=audit_id,
            timestamp=ts,
            all_passed=all_passed,
            passed_count=passed_count,
            total_checks=len(checks),
            checks=checks,
            rollback_verified=rollback_ok,
            signature=sig,
        )

        logger.info(
            f"[PolicyAuditor] Audit complete: {passed_count}/{len(checks)} checks passed, "
            f"Rollback verified={rollback_ok}, Overall Passed={all_passed}"
        )
        return report


policy_auditor = PolicyAuditor()
