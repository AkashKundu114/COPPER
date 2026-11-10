"""Unified Data Classification and Governance Policy System for COPPER.

Enforces explicit access, retention, encryption, and transmission controls
across all stored and in-flight data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class DataClassification(str, Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    PERSONAL = "personal"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


@dataclass(frozen=True)
class GovernancePolicy:
    classification: DataClassification
    description: str
    allowed_external_egress: bool
    encryption_at_rest_required: bool
    encryption_in_transit_required: bool
    pii_redaction_required: bool
    verifiable_deletion_required: bool
    default_retention_days: int | None  # None indicates indefinite retention

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["classification"] = self.classification.value
        return data


GOVERNANCE_POLICIES: dict[DataClassification, GovernancePolicy] = {
    DataClassification.PUBLIC: GovernancePolicy(
        classification=DataClassification.PUBLIC,
        description="Publicly consumable documentation, release notes, and open system capabilities.",
        allowed_external_egress=True,
        encryption_at_rest_required=False,
        encryption_in_transit_required=True,
        pii_redaction_required=False,
        verifiable_deletion_required=False,
        default_retention_days=None,
    ),
    DataClassification.INTERNAL: GovernancePolicy(
        classification=DataClassification.INTERNAL,
        description="System metrics, routing analytics, internal agent codenames, and non-sensitive operational telemetry.",
        allowed_external_egress=False,
        encryption_at_rest_required=False,
        encryption_in_transit_required=True,
        pii_redaction_required=True,
        verifiable_deletion_required=False,
        default_retention_days=365,
    ),
    DataClassification.PERSONAL: GovernancePolicy(
        classification=DataClassification.PERSONAL,
        description="Standard user-identifiable data: usernames, general chat history, preferences, and local filesystem paths.",
        allowed_external_egress=False,
        encryption_at_rest_required=True,
        encryption_in_transit_required=True,
        pii_redaction_required=True,
        verifiable_deletion_required=True,
        default_retention_days=180,
    ),
    DataClassification.SENSITIVE: GovernancePolicy(
        classification=DataClassification.SENSITIVE,
        description="Sensitive user information: emails, phone numbers, IP addresses, confidential epistemic memories, and private notes.",
        allowed_external_egress=False,
        encryption_at_rest_required=True,
        encryption_in_transit_required=True,
        pii_redaction_required=True,
        verifiable_deletion_required=True,
        default_retention_days=90,
    ),
    DataClassification.RESTRICTED: GovernancePolicy(
        classification=DataClassification.RESTRICTED,
        description="Critical secrets: passwords, API keys, private keys, bearer tokens, credit cards, and SSNs. Strictly isolated.",
        allowed_external_egress=False,
        encryption_at_rest_required=True,
        encryption_in_transit_required=True,
        pii_redaction_required=True,
        verifiable_deletion_required=True,
        default_retention_days=30,
    ),
}


def get_governance_policy(classification: DataClassification | str) -> GovernancePolicy:
    if isinstance(classification, str):
        try:
            classification = DataClassification(classification.lower())
        except ValueError:
            classification = DataClassification.INTERNAL
    return GOVERNANCE_POLICIES.get(classification, GOVERNANCE_POLICIES[DataClassification.INTERNAL])
