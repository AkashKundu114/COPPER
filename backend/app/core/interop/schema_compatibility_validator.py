"""API Contract & Schema Evolution Compatibility Validator for C.O.P.P.E.R.

Detects breaking schema changes between contract versions (removed fields, widened
required sets, incompatible type mutations) to guarantee strict backward compatibility
across REST, MCP, and Agent integration boundaries.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.logger import logger


@dataclass
class SchemaDiffViolation:
    field_path: str
    change_type: str  # "REMOVED_FIELD" | "TYPE_MISMATCH" | "NEW_REQUIRED_FIELD"
    details: str


@dataclass
class SchemaEvolutionReport:
    report_id: str
    timestamp: float
    is_backward_compatible: bool
    violations: list[SchemaDiffViolation]
    warnings: list[str]
    old_version: str
    new_version: str
    signature: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SchemaCompatibilityValidator:
    """Verifies schema evolutions against strict backward compatibility rules."""

    @staticmethod
    def compare_schemas(
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
        old_version: str = "v1",
        new_version: str = "v2",
    ) -> SchemaEvolutionReport:
        """Compares two JSON schema models and detects breaking changes."""
        violations: list[SchemaDiffViolation] = []
        warnings: list[str] = []

        old_props = old_schema.get("properties", {})
        new_props = new_schema.get("properties", {})
        old_required = set(old_schema.get("required", []))
        new_required = set(new_schema.get("required", []))

        # 1. Check for removed fields (Breaking)
        for field_name in old_props:
            if field_name not in new_props:
                violations.append(
                    SchemaDiffViolation(
                        field_path=field_name,
                        change_type="REMOVED_FIELD",
                        details=f"Field '{field_name}' existed in {old_version} but was removed in {new_version}.",
                    )
                )

        # 2. Check for type mutations (Breaking if incompatible)
        for field_name, old_meta in old_props.items():
            if field_name in new_props:
                new_meta = new_props[field_name]
                old_type = old_meta.get("type")
                new_type = new_meta.get("type")
                if old_type and new_type and old_type != new_type:
                    violations.append(
                        SchemaDiffViolation(
                            field_path=field_name,
                            change_type="TYPE_MISMATCH",
                            details=f"Field '{field_name}' changed type from '{old_type}' to '{new_type}'.",
                        )
                    )

        # 3. Check for newly introduced required fields without defaults (Breaking)
        newly_required = new_required - old_required
        for field_name in newly_required:
            if field_name not in old_props:
                violations.append(
                    SchemaDiffViolation(
                        field_path=field_name,
                        change_type="NEW_REQUIRED_FIELD",
                        details=f"New required field '{field_name}' added to {new_version} without backward-compatible default.",
                    )
                )

        # 4. Check for added optional fields (Non-breaking - generates info warning)
        for field_name in new_props:
            if field_name not in old_props and field_name not in new_required:
                warnings.append(f"Non-breaking: Optional field '{field_name}' added in {new_version}.")

        is_compatible = len(violations) == 0
        now = time.time()
        rep_id = f"SCH-EVO-{hashlib.sha256(str(now).encode()).hexdigest()[:12].upper()}"
        sig = hashlib.sha256(f"{rep_id}:{is_compatible}:{len(violations)}".encode()).hexdigest()

        report = SchemaEvolutionReport(
            report_id=rep_id,
            timestamp=now,
            is_backward_compatible=is_compatible,
            violations=violations,
            warnings=warnings,
            old_version=old_version,
            new_version=new_version,
            signature=sig,
        )

        logger.info(
            f"[SchemaCompatibilityValidator] Evolution check ({old_version} -> {new_version}): "
            f"Compatible={is_compatible}, Violations={len(violations)}"
        )
        return report


schema_compatibility_validator = SchemaCompatibilityValidator()
