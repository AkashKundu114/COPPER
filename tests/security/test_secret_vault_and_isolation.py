"""Tests for SecretVault and Dynamic Credential Isolation."""

import pytest

from app.core.data_firewall import classify_and_redact, redact
from app.core.security.secret_vault import secret_vault


def test_secret_vault_storage_and_retrieval():
    """Verify secrets can be stored and retrieved by key."""
    secret_vault.store_secret("PROD_DATABASE_KEY", "super_secret_db_pass_9988", "Production DB credentials")

    retrieved = secret_vault.get_secret("PROD_DATABASE_KEY")
    assert retrieved == "super_secret_db_pass_9988"

    assert secret_vault.get_secret("NON_EXISTENT_KEY") is None


def test_secret_vault_metadata_does_not_leak_values():
    """Verify list_secrets returns metadata without raw secret values."""
    secret_vault.store_secret("STRIPE_SECRET_KEY", "sk_live_veryconfidential12345", "Payment gateway key")

    metadata_list = secret_vault.list_secrets()
    keys = [item["key"] for item in metadata_list]
    assert "STRIPE_SECRET_KEY" in keys

    # Verify no value field exists in metadata
    for item in metadata_list:
        assert "value" not in item
        assert "super_secret" not in str(item)
        assert "sk_live" not in str(item)


def test_secret_vault_binds_to_data_firewall_redaction():
    """Verify that stored secrets are dynamically redacted by DataFirewall."""
    raw_secret = "copper_vault_token_xyz987"
    secret_vault.store_secret("VAULT_TEST_KEY", raw_secret, "Test secret for redaction")

    # Now simulate a log or message containing this secret
    log_message = f"Connecting to external API with token: {raw_secret} for session."
    redacted_message = redact(log_message)

    assert raw_secret not in redacted_message
    assert "•••VAULT_SECRET_REDACTED•••" in redacted_message

    firewall_res = classify_and_redact(log_message)
    assert raw_secret not in firewall_res.redacted_text
    assert firewall_res.classification.value == "secret"


def test_secret_deletion():
    """Verify secret deletion."""
    secret_vault.store_secret("TEMP_KEY", "temp_val_12345", "Temporary key")
    assert secret_vault.get_secret("TEMP_KEY") == "temp_val_12345"

    deleted = secret_vault.delete_secret("TEMP_KEY")
    assert deleted is True
    assert secret_vault.get_secret("TEMP_KEY") is None
