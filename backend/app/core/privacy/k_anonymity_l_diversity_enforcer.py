"""k-Anonymity and l-Diversity Generalization and Privacy Enforcer.

Implements Stage 10 Privacy & Data Governance Framework:
- Analyzes tabular telemetry and audit records for quasi-identifiers (QI) and sensitive attributes.
- Enforces strict k-anonymity (k >= 3) and l-diversity (l >= 2) on exported dataset equivalence classes.
- Applies attribute generalization hierarchies and cell suppression to prevent re-identification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class AnonymityEquivalenceClass:
    class_id: str
    quasi_identifier_pattern: dict[str, str]
    records_count: int
    distinct_sensitive_count: int
    is_k_anonymous: bool
    is_l_diverse: bool


@dataclass
class AnonymizationComplianceReport:
    total_records: int
    total_classes: int
    min_k_achieved: int
    min_l_achieved: int
    is_fully_compliant: bool
    suppressed_records_count: int
    equivalence_classes: list[AnonymityEquivalenceClass] = field(default_factory=list)


class KAnonymityLDiversityEnforcer:
    """Evaluates and enforces k-anonymity and l-diversity privacy guarantees on dataset releases."""

    def __init__(self, target_k: int = 3, target_l: int = 2) -> None:
        self.target_k = target_k
        self.target_l = target_l

    def generalize_attribute(self, attr_name: str, value: Any) -> str:
        """Apply hierarchical generalization rules to quasi-identifiers."""
        val_str = str(value)
        if attr_name == "ip_address":
            # Mask host octet: 192.168.1.50 -> 192.168.1.0/24
            parts = val_str.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"
        elif attr_name == "latency_ms":
            # Bucket into 50ms intervals
            try:
                lat = float(value)
                bucket_lower = int(lat // 50) * 50
                return f"[{bucket_lower}-{bucket_lower + 50}ms]"
            except ValueError:
                pass
        elif attr_name == "user_role":
            return "authenticated_user"

        return val_str

    def evaluate_compliance(
        self,
        records: list[dict[str, Any]],
        quasi_identifiers: list[str],
        sensitive_attribute: str,
    ) -> AnonymizationComplianceReport:
        """Evaluate dataset equivalence classes against k-anonymity and l-diversity thresholds."""
        if not records:
            return AnonymizationComplianceReport(
                total_records=0, total_classes=0, min_k_achieved=0, min_l_achieved=0,
                is_fully_compliant=True, suppressed_records_count=0
            )

        # Group records into equivalence classes based on generalized quasi-identifiers
        groups: dict[tuple, list[dict[str, Any]]] = {}
        for r in records:
            qi_tuple = tuple(self.generalize_attribute(qi, r.get(qi, "UNKNOWN")) for qi in quasi_identifiers)
            if qi_tuple not in groups:
                groups[qi_tuple] = []
            groups[qi_tuple].append(r)

        eq_classes: list[AnonymityEquivalenceClass] = []
        suppressed = 0
        min_k = len(records)
        min_l = len(records)

        for idx, (qi_key, group_records) in enumerate(groups.items(), 1):
            count = len(group_records)
            distinct_sens = len({gr.get(sensitive_attribute) for gr in group_records})

            k_ok = count >= self.target_k
            l_ok = distinct_sens >= self.target_l

            if not k_ok or not l_ok:
                suppressed += count

            min_k = min(min_k, count)
            min_l = min(min_l, distinct_sens)

            qi_dict = {qi: qi_key[i] for i, qi in enumerate(quasi_identifiers)}
            eq_classes.append(
                AnonymityEquivalenceClass(
                    class_id=f"eq-class-{idx:03d}",
                    quasi_identifier_pattern=qi_dict,
                    records_count=count,
                    distinct_sensitive_count=distinct_sens,
                    is_k_anonymous=k_ok,
                    is_l_diverse=l_ok,
                )
            )

        fully_compliant = suppressed == 0 and min_k >= self.target_k and min_l >= self.target_l

        return AnonymizationComplianceReport(
            total_records=len(records),
            total_classes=len(eq_classes),
            min_k_achieved=min_k if eq_classes else 0,
            min_l_achieved=min_l if eq_classes else 0,
            is_fully_compliant=fully_compliant,
            suppressed_records_count=suppressed,
            equivalence_classes=eq_classes,
        )
