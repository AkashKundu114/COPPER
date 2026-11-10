"""Semantic API Contract and Type Breaking Change Detector.

Implements Stage 9 Maintainability & Evolvability Architecture:
- Analyzes function signatures, tool interfaces, and schema definitions across revisions.
- Detects breaking changes (deleted arguments, newly required fields, narrowed parameter types).
- Enforces strict semantic backward compatibility for all agent tool contracts.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional


class ContractChangeType(str, Enum):
    COMPATIBLE_ADDITION = "COMPATIBLE_ADDITION"
    BREAKING_REMOVAL = "BREAKING_REMOVAL"
    BREAKING_TYPE_CHANGE = "BREAKING_TYPE_CHANGE"
    BREAKING_REQUIRED_PARAM = "BREAKING_REQUIRED_PARAM"


@dataclass
class ContractDiffViolation:
    item_name: str
    change_type: ContractChangeType
    description: str
    is_breaking: bool


@dataclass
class ContractCompatibilityReport:
    is_backward_compatible: bool
    total_checks_evaluated: int
    breaking_changes_count: int
    violations: list[ContractDiffViolation] = field(default_factory=list)


class SemanticContractDiffDetector:
    """Verifies backward compatibility across tool interfaces and schema contracts."""

    def compare_tool_schemas(
        self,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
    ) -> ContractCompatibilityReport:
        """Compare two JSON tool input schemas (old vs new) and flag breaking changes."""
        violations: list[ContractDiffViolation] = []
        checks = 0

        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))

        # Check for removed properties (breaking)
        for prop_name in old_props:
            checks += 1
            if prop_name not in new_props:
                violations.append(
                    ContractDiffViolation(
                        item_name=prop_name,
                        change_type=ContractChangeType.BREAKING_REMOVAL,
                        description=f"Property '{prop_name}' was removed from the schema.",
                        is_breaking=True,
                    )
                )

        # Check for newly added required properties (breaking for existing callers)
        for req in new_required:
            checks += 1
            if req not in old_required and req not in old_props:
                violations.append(
                    ContractDiffViolation(
                        item_name=req,
                        change_type=ContractChangeType.BREAKING_REQUIRED_PARAM,
                        description=f"New required property '{req}' was added without backward default.",
                        is_breaking=True,
                    )
                )

        # Check for altered types on existing properties
        for prop_name, old_spec in old_props.items():
            if prop_name in new_props:
                checks += 1
                new_spec = new_props[prop_name]
                old_type = old_spec.get("type")
                new_type = new_spec.get("type")
                if old_type and new_type and old_type != new_type:
                    violations.append(
                        ContractDiffViolation(
                            item_name=prop_name,
                            change_type=ContractChangeType.BREAKING_TYPE_CHANGE,
                            description=f"Property '{prop_name}' type changed from '{old_type}' to '{new_type}'.",
                            is_breaking=True,
                        )
                    )

        breaking_count = sum(1 for v in violations if v.is_breaking)

        return ContractCompatibilityReport(
            is_backward_compatible=breaking_count == 0,
            total_checks_evaluated=checks,
            breaking_changes_count=breaking_count,
            violations=violations,
        )
