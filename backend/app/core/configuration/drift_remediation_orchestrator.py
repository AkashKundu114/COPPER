"""Autonomous Configuration Drift Remediation and State Harmonizer.

Implements Stage 9 Configuration & Policy Management Architecture:
- Detects unauthorized runtime mutations and divergence from declarative config manifests.
- Computes granular attribute-level drift deltas across active settings.
- Automatically executes self-healing reconciliation to restore pristine state baselines.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class ConfigurationDriftDelta:
    parameter_path: str
    baseline_value: Any
    current_value: Any
    drift_detected: bool
    remediation_action: str


@dataclass
class DriftRemediationReport:
    total_parameters_audited: int
    drifts_detected_count: int
    remediations_applied_count: int
    harmonized: bool
    drift_deltas: list[ConfigurationDriftDelta] = field(default_factory=list)


class DriftRemediationOrchestrator:
    """Detects and reconciles runtime configuration drift against declared baselines."""

    def __init__(self, baseline_manifest: Optional[dict[str, Any]] = None) -> None:
        self.baseline_manifest: dict[str, Any] = copy.deepcopy(baseline_manifest or {
            "model_runtime.max_vram_gb": 8.0,
            "model_runtime.default_quantization": "INT4",
            "security.zero_trust_strict": True,
            "security.mcp_sandbox_enabled": True,
            "finops.power_cap_watts": 160.0,
            "network.local_first_mode": True,
        })
        self.active_runtime_config: dict[str, Any] = copy.deepcopy(self.baseline_manifest)

    def set_runtime_override(self, key: str, value: Any) -> None:
        """Simulate or apply a runtime modification."""
        self.active_runtime_config[key] = value

    def audit_and_remediate(self, auto_reconcile: bool = True) -> DriftRemediationReport:
        """Scan active configuration for drift and restore baseline values if requested."""
        deltas: list[ConfigurationDriftDelta] = []
        drifts = 0
        remediated = 0

        for key, base_val in self.baseline_manifest.items():
            curr_val = self.active_runtime_config.get(key)
            if curr_val != base_val:
                drifts += 1
                action = f"Reset '{key}' from {curr_val} back to baseline {base_val}"
                if auto_reconcile:
                    self.active_runtime_config[key] = copy.deepcopy(base_val)
                    remediated += 1
                    action += " [APPLIED]"

                deltas.append(
                    ConfigurationDriftDelta(
                        parameter_path=key,
                        baseline_value=base_val,
                        current_value=curr_val,
                        drift_detected=True,
                        remediation_action=action,
                    )
                )

        harmonized = (drifts == remediated) if auto_reconcile else (drifts == 0)

        return DriftRemediationReport(
            total_parameters_audited=len(self.baseline_manifest),
            drifts_detected_count=drifts,
            remediations_applied_count=remediated,
            harmonized=harmonized,
            drift_deltas=deltas,
        )
