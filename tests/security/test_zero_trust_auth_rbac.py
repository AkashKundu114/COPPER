"""Tests for Zero-Trust Authentication, Key Verification, and RBAC/ABAC."""

import pytest
from fastapi.testclient import TestClient

from app.core.config import NetworkMode, settings
from app.core.security.access_control import (
    ABACContext,
    Permission,
    Role,
    access_controller,
)
from app.core.security.auth import Principal, PrincipalType, key_manager
from app.main import app

client = TestClient(app)


def test_key_manager_constant_time_verification():
    """Verify KeyManager generates and verifies operator keys with constant-time equality."""
    key = key_manager.get_or_create_operator_key()
    assert len(key) >= 32
    assert key_manager.verify_key(key) is True
    assert key_manager.verify_key("wrong_key_attempt") is False
    assert key_manager.verify_key("") is False


def test_auth_verify_endpoint_with_valid_and_invalid_keys():
    """Verify /api/v1/auth/verify endpoint."""
    valid_key = key_manager.get_or_create_operator_key()
    res_valid = client.post("/api/v1/auth/verify", json={"token": valid_key})
    assert res_valid.status_code == 200
    assert res_valid.json()["valid"] is True
    assert res_valid.json()["type"] == "operator_key"

    res_invalid = client.post("/api/v1/auth/verify", json={"token": "bogus_token_12345"})
    assert res_invalid.status_code == 200
    assert res_invalid.json()["valid"] is False


def test_unauthorized_api_requests_when_strict_auth_enforced(monkeypatch):
    """Verify unauthorized requests are rejected with 401 when AUTH_ENFORCED is active."""
    monkeypatch.setattr(settings, "AUTH_ENFORCED", True)

    # Calling protected endpoint without token should return 401
    res_unauth = client.get("/api/v1/auth/me")
    assert res_unauth.status_code == 401
    assert "Authentication required" in res_unauth.json()["detail"]

    # Calling with invalid token should return 401
    res_bad = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_secret_key"},
    )
    assert res_bad.status_code == 401

    # Calling with valid token should succeed
    valid_key = key_manager.get_or_create_operator_key()
    res_ok = client.get(
        "/api/v1/auth/me",
        headers={"X-API-Key": valid_key},
    )
    assert res_ok.status_code == 200
    assert res_ok.json()["status"] == "authenticated"
    assert res_ok.json()["role"] == "admin"


def test_rbac_privilege_escalation_prevention():
    """Verify roles cannot escalate beyond granted permissions."""
    read_only_principal = Principal(
        id="auditor_user",
        principal_type=PrincipalType.OPERATOR,
        role=Role.READ_ONLY.value,
    )

    # READ_ONLY role can read system and agents
    is_auth, _ = access_controller.is_authorized(read_only_principal, Permission.SYSTEM_READ)
    assert is_auth is True

    # READ_ONLY role CANNOT execute tools
    is_auth, err = access_controller.is_authorized(read_only_principal, Permission.TOOL_EXECUTE_SAFE)
    assert is_auth is False
    assert "lacks required permission" in err

    # READ_ONLY role CANNOT delete audit logs
    is_auth, err = access_controller.is_authorized(read_only_principal, Permission.AUDIT_DELETE)
    assert is_auth is False


def test_abac_destructive_audit_requires_operator_confirmation():
    """Verify ABAC rejects audit destruction without explicit confirmation."""
    admin_principal = Principal(
        id="admin_user",
        principal_type=PrincipalType.OPERATOR,
        role=Role.ADMIN.value,
        scopes={"*"},  # Even with wildcard, ABAC context constraints are evaluated
    )

    unconfirmed_ctx = ABACContext(operator_confirmed=False)
    confirmed_ctx = ABACContext(operator_confirmed=True)

    # Standard admin with wildcard passes, but when evaluating standard role without wildcard:
    standard_admin = Principal(
        id="std_admin",
        principal_type=PrincipalType.OPERATOR,
        role=Role.ADMIN.value,
        scopes=set(),
    )
    is_auth_unconfirmed, err = access_controller.is_authorized(
        standard_admin,
        Permission.AUDIT_DELETE,
        context=unconfirmed_ctx,
    )
    assert is_auth_unconfirmed is False
    assert "requires ADMIN role with explicit operator confirmation" in err

    is_auth_confirmed, _ = access_controller.is_authorized(
        standard_admin,
        Permission.AUDIT_DELETE,
        context=confirmed_ctx,
    )
    assert is_auth_confirmed is True


def test_abac_airgap_egress_blocking():
    """Verify ABAC blocks network-accessing tools when in OFFLINE_AIRGAP mode."""
    operator_principal = Principal(
        id="op_user",
        principal_type=PrincipalType.OPERATOR,
        role=Role.OPERATOR.value,
        scopes=set(),
    )

    airgap_ctx = ABACContext(network_mode=NetworkMode.OFFLINE_AIRGAP)
    is_auth, err = access_controller.is_authorized(
        operator_principal,
        Permission.TOOL_EXECUTE_MODERATE,
        context=airgap_ctx,
    )
    assert is_auth is False
    assert "OFFLINE_AIRGAP policy" in err
