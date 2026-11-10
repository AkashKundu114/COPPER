"""Tests for Cryptographic AgentTokens and Zero-Trust Tool Authorization."""

import pytest

from app.ai.tools.executor import tool_executor
from app.ai.tools.registry import tool_registry
from app.core.security.access_control import Permission, Role
from app.core.security.agent_token import agent_token_service
from app.core.security.auth import Principal, PrincipalType
from app.core.security.tool_policy import tool_authorization_policy


def test_agent_token_generation_and_verification():
    """Verify AgentToken generation, HMAC signature, and payload integrity."""
    token = agent_token_service.issue_token(
        agent_id="coding_agent",
        agent_type="coding",
        allowed_tools=["python_execute", "file_read"],
        ttl_seconds=60,
        max_steps=5,
    )
    assert token.startswith("agtok.")

    payload = agent_token_service.verify_token(token)
    assert payload is not None
    assert payload.agent_id == "coding_agent"
    assert payload.agent_type == "coding"
    assert payload.allowed_tools == ["python_execute", "file_read"]
    assert payload.max_steps == 5


def test_agent_token_tamper_detection():
    """Verify modified or forged AgentTokens fail verification."""
    token = agent_token_service.issue_token(
        agent_id="reminder_agent",
        agent_type="reminder",
        allowed_tools=["calendar_list"],
    )

    parts = token.split(".")
    # Tamper with the base64 signature
    tampered_sig = parts[0] + "." + parts[1] + "." + parts[2][:-4] + "AAAA"
    assert agent_token_service.verify_token(tampered_sig) is None

    # Tamper with payload
    tampered_payload = parts[0] + ".eyJhZ2VudF9pZCI6ImFkbWluIn0." + parts[2]
    assert agent_token_service.verify_token(tampered_payload) is None


def test_agent_token_expiration():
    """Verify expired AgentTokens are rejected."""
    token = agent_token_service.issue_token(
        agent_id="test_agent",
        agent_type="test",
        allowed_tools=["file_read"],
        ttl_seconds=-1,  # Expired immediately in the past
    )
    assert agent_token_service.verify_token(token) is None


@pytest.mark.asyncio
async def test_cross_agent_permission_violation_rejection():
    """Verify an agent cannot execute tools outside its granted scope."""
    # Issue token granting ONLY calendar_list to reminder_agent
    restricted_token = agent_token_service.issue_token(
        agent_id="reminder_agent",
        agent_type="reminder",
        allowed_tools=["calendar_list"],
    )

    # Attempt to execute file_write or shell_execute using this token
    result = await tool_executor.execute(
        tool_name="shell_execute",
        arguments={"command": "dir"},
        context={
            "agent": "reminder_agent",
            "agent_token": restricted_token,
        },
    )
    assert result.success is False
    assert "Tool authorization denied" in result.error
    assert "outside granted capability scope" in result.error


@pytest.mark.asyncio
async def test_tool_authorization_policy_allows_authorized_tools():
    """Verify authorized tools execute normally under granted scope."""
    authorized_token = agent_token_service.issue_token(
        agent_id="research_agent",
        agent_type="research",
        allowed_tools=["file_read"],
    )

    file_read_tool = tool_registry.get("file_read")
    assert file_read_tool is not None

    is_auth, err = tool_authorization_policy.authorize_tool_call(
        file_read_tool,
        {"path": "README.md"},
        context={
            "agent": "research_agent",
            "agent_token": authorized_token,
        },
    )
    assert is_auth is True
    assert err is None


@pytest.mark.asyncio
async def test_direct_principal_rbac_gating_on_tool():
    """Verify principal RBAC is enforced when principal is in context."""
    auditor_principal = Principal(
        id="auditor_user",
        principal_type=PrincipalType.OPERATOR,
        role=Role.AUDITOR.value,
    )
    shell_tool = tool_registry.get("shell_execute")
    assert shell_tool is not None

    is_auth, err = tool_authorization_policy.authorize_tool_call(
        shell_tool,
        {"command": "echo test"},
        context={"principal": auditor_principal},
    )
    assert is_auth is False
    assert "unauthorized for tool 'shell_execute'" in err
