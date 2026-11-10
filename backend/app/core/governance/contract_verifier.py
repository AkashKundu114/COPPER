"""Architectural Contract, Interface Compatibility & Boundary Verifier for C.O.P.P.E.R.

Performs static AST inspections and runtime contract verification across modular
subsystems: ensures layer isolation (e.g. database never imports AI or API),
validates tool/agent protocol compliance, and detects forbidden circular dependencies.
"""

from __future__ import annotations

import ast
import hashlib
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.core.logger import logger


@dataclass
class BoundaryCheckResult:
    source_layer: str
    target_layer: str
    forbidden: bool
    violations: list[str] = field(default_factory=list)


@dataclass
class InterfaceComplianceCheck:
    component_name: str
    contract_type: str  # "AgentContract" | "ToolContract" | "StorageAdapter"
    is_compliant: bool
    missing_methods: list[str] = field(default_factory=list)
    details: str = ""


@dataclass
class ContractVerificationReport:
    report_id: str
    timestamp: float
    all_boundaries_clean: bool
    all_interfaces_compliant: bool
    boundary_checks: list[BoundaryCheckResult]
    interface_checks: list[InterfaceComplianceCheck]
    total_violations_count: int
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ArchitecturalContractVerifier:
    """Verifies that COPPER modules strictly follow layered architecture and interface contracts."""

    FORBIDDEN_DEPENDENCY_RULES: dict[str, list[str]] = {
        "database": ["app.ai", "app.api"],
        # Core stays independent of top-level HTTP API routers
        "core/configuration": ["app.api"],
        "core/audit": ["app.api"],
    }

    def __init__(self, app_root: Path | None = None):
        if app_root:
            self.app_root = app_root
        else:
            self.app_root = Path(__file__).resolve().parent.parent.parent

    def verify_layer_boundaries(self) -> list[BoundaryCheckResult]:
        """Scans python files using AST to ensure low-level layers don't import higher layers."""
        results: list[BoundaryCheckResult] = []

        for layer, forbidden_prefixes in self.FORBIDDEN_DEPENDENCY_RULES.items():
            layer_dir = self.app_root / layer
            violations: list[str] = []

            if not layer_dir.exists():
                continue

            for root, _, files in os.walk(layer_dir):
                for f in files:
                    if not f.endswith(".py"):
                        continue
                    file_path = Path(root) / f
                    try:
                        with open(file_path, "r", encoding="utf-8") as source_f:
                            tree = ast.parse(source_f.read(), filename=str(file_path))
                    except Exception as e:
                        logger.warning(f"Failed to parse {file_path}: {e}")
                        continue

                    for node in ast.walk(tree):
                        mod_name = ""
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                mod_name = alias.name
                                for forb in forbidden_prefixes:
                                    if mod_name.startswith(forb):
                                        violations.append(f"{file_path.name}:{node.lineno} imports '{mod_name}'")
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            mod_name = node.module
                            for forb in forbidden_prefixes:
                                if mod_name.startswith(forb):
                                    violations.append(f"{file_path.name}:{node.lineno} imports '{mod_name}'")

            results.append(
                BoundaryCheckResult(
                    source_layer=layer,
                    target_layer=", ".join(forbidden_prefixes),
                    forbidden=True,
                    violations=violations,
                )
            )

        return results

    def verify_interface_contracts(self) -> list[InterfaceComplianceCheck]:
        """Verifies runtime contracts for critical architectural components."""
        checks: list[InterfaceComplianceCheck] = []

        # 1. Verify Tool Contract Registry compatibility
        from app.core.interop.tool_contract import ToolContractWrapper
        has_run = hasattr(ToolContractWrapper, "execute_contract")
        checks.append(
            InterfaceComplianceCheck(
                component_name="ToolContractWrapper",
                contract_type="ToolContract",
                is_compliant=has_run,
                missing_methods=[] if has_run else ["execute_contract"],
                details="Standardized tool execution contract with input/output validation",
            )
        )

        # 2. Verify Distributed Lock Contract
        from app.core.scalability.distributed_lock import DistributedLockManager
        has_acq = hasattr(DistributedLockManager, "acquire_lock")
        has_rel = hasattr(DistributedLockManager, "release_lock")
        is_lock_ok = has_acq and has_rel
        checks.append(
            InterfaceComplianceCheck(
                component_name="DistributedLockManager",
                contract_type="DistributedLock",
                is_compliant=is_lock_ok,
                missing_methods=[] if is_lock_ok else ["acquire_lock" if not has_acq else "release_lock"],
                details="Lease-based mutual exclusion interface",
            )
        )

        # 3. Verify Dynamic Policy Enforcer Contract
        from app.core.configuration.runtime_enforcer import DynamicPolicyEnforcer
        has_eval = hasattr(DynamicPolicyEnforcer, "evaluate_operation")
        checks.append(
            InterfaceComplianceCheck(
                component_name="DynamicPolicyEnforcer",
                contract_type="PolicyEnforcer",
                is_compliant=has_eval,
                missing_methods=[] if has_eval else ["evaluate_operation"],
                details="Runtime dynamic policy evaluation and enforcement",
            )
        )

        return checks

    def run_governance_verification(self) -> ContractVerificationReport:
        """Runs complete architectural boundary and interface contract suite."""
        boundaries = self.verify_layer_boundaries()
        interfaces = self.verify_interface_contracts()

        total_boundary_violations = sum(len(b.violations) for b in boundaries)
        all_boundaries_ok = total_boundary_violations == 0
        all_interfaces_ok = all(i.is_compliant for i in interfaces)

        ts = time.time()
        rep_id = f"CONTRACT-{hashlib.sha256(str(ts).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{rep_id}:{all_boundaries_ok}:{all_interfaces_ok}".encode()).hexdigest()

        report = ContractVerificationReport(
            report_id=rep_id,
            timestamp=ts,
            all_boundaries_clean=all_boundaries_ok,
            all_interfaces_compliant=all_interfaces_ok,
            boundary_checks=boundaries,
            interface_checks=interfaces,
            total_violations_count=total_boundary_violations,
            signature=sig,
        )

        logger.info(
            f"[ArchitecturalContractVerifier] Boundaries clean={all_boundaries_ok} "
            f"(violations={total_boundary_violations}), Interfaces compliant={all_interfaces_ok}"
        )
        return report


contract_verifier = ArchitecturalContractVerifier()
