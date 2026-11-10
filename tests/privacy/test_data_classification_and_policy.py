import pytest

from app.core.privacy.classification import (
    DataClassification,
    GovernancePolicy,
    GOVERNANCE_POLICIES,
    get_governance_policy,
)


def test_five_tier_classification_coverage():
    """Verify all 5 required classifications exist with explicit governance policies."""
    assert len(GOVERNANCE_POLICIES) == 5
    for cat in [
        DataClassification.PUBLIC,
        DataClassification.INTERNAL,
        DataClassification.PERSONAL,
        DataClassification.SENSITIVE,
        DataClassification.RESTRICTED,
    ]:
        assert cat in GOVERNANCE_POLICIES
        policy = GOVERNANCE_POLICIES[cat]
        assert isinstance(policy, GovernancePolicy)
        assert policy.classification == cat


def test_restricted_classification_rules():
    """Verify RESTRICTED data (passwords, private keys, credit cards) has strictest rules."""
    policy = get_governance_policy(DataClassification.RESTRICTED)
    assert policy.allowed_external_egress is False
    assert policy.encryption_at_rest_required is True
    assert policy.encryption_in_transit_required is True
    assert policy.pii_redaction_required is True
    assert policy.verifiable_deletion_required is True
    assert policy.default_retention_days == 30


def test_public_classification_rules():
    """Verify PUBLIC data permits external egress and has indefinite retention."""
    policy = get_governance_policy(DataClassification.PUBLIC)
    assert policy.allowed_external_egress is True
    assert policy.default_retention_days is None
    assert policy.verifiable_deletion_required is False


def test_policy_lookup_case_insensitivity_and_fallback():
    """Verify policy resolution is case-insensitive and gracefully defaults on invalid input."""
    assert get_governance_policy("sensitive").classification == DataClassification.SENSITIVE
    assert get_governance_policy("RESTRICTED").classification == DataClassification.RESTRICTED
    assert get_governance_policy("invalid_cat").classification == DataClassification.INTERNAL
