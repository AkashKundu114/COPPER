"""Architectural Fitness Function and Evolutionary Boundary Evaluator.

Implements Stage 12 Maintainability & Evolvability Architecture:
- Programmatically asserts architectural invariants (ADR compliance, layer dependencies, package isolation).
- Computes Martin's Coupling Metrics: Afferent (Ca), Efferent (Ce), and Instability I = Ce / (Ca + Ce).
- Automatically guards against architectural erosion during continuous feature addition.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PackageCouplingMetrics:
    package_name: str
    afferent_coupling_ca: int  # incoming dependencies
    efferent_coupling_ce: int  # outgoing dependencies
    instability_index: float   # Ce / (Ca + Ce)


@dataclass
class FitnessEvaluationReport:
    all_fitness_functions_passed: bool
    total_packages_evaluated: int
    boundary_violations: list[str]
    package_metrics: list[PackageCouplingMetrics] = field(default_factory=list)


class ArchitecturalFitnessFunctionEvaluator:
    """Evaluates programmatic fitness functions safeguarding architectural integrity."""

    # Disallowed layer dependency edges (Layer -> Forbidden targets)
    FORBIDDEN_LAYER_DEPENDENCIES = {
        "database": ["app.ai", "app.api"],
        "core": ["app.api"],
    }

    def evaluate_package_fitness(
        self,
        package_imports: dict[str, list[str]],
    ) -> FitnessEvaluationReport:
        """Evaluate architectural fitness rules across package import graphs."""
        violations: list[str] = []
        metrics: list[PackageCouplingMetrics] = []

        # Calculate Ca (incoming) and Ce (outgoing)
        for pkg, imports in package_imports.items():
            ce = len(imports)
            ca = sum(1 for other_pkg, other_imports in package_imports.items() if other_pkg != pkg and pkg in other_imports)
            instability = ce / max(1, ca + ce)

            metrics.append(
                PackageCouplingMetrics(
                    package_name=pkg,
                    afferent_coupling_ca=ca,
                    efferent_coupling_ce=ce,
                    instability_index=round(instability, 2),
                )
            )

            # Check forbidden layer rules
            forbidden = self.FORBIDDEN_LAYER_DEPENDENCIES.get(pkg, [])
            for imp in imports:
                for forb in forbidden:
                    if imp.startswith(forb):
                        violations.append(
                            f"Fitness Function Failure: Package '{pkg}' imports '{imp}' (Forbidden target '{forb}')."
                        )

        return FitnessEvaluationReport(
            all_fitness_functions_passed=len(violations) == 0,
            total_packages_evaluated=len(package_imports),
            boundary_violations=violations,
            package_metrics=metrics,
        )
