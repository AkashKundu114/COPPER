"""Role-Based (RBAC) and Attribute-Based Access Control (ABAC) Engine for COPPER.

Enforces least-privilege policies across agents, models, tools, and endpoints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.core.config import NetworkMode, settings
from app.core.logger import logger
from app.core.security.auth import Principal, PrincipalType


class Role(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    AGENT = "agent"
    AUDITOR = "auditor"
    READ_ONLY = "read_only"


class Permission(str, Enum):
    # System & Audit
    SYSTEM_READ = "system:read"
    SYSTEM_WRITE = "system:write"
    AUDIT_READ = "audit:read"
    AUDIT_DELETE = "audit:delete"
    AUDIT_EXPORT = "audit:export"

    # Agent Lifecycle
    AGENT_READ = "agent:read"
    AGENT_ACTIVATE = "agent:activate"
    AGENT_MODIFY = "agent:modify"
    AGENT_EXECUTE = "agent:execute"

    # Tool Execution
    TOOL_EXECUTE_SAFE = "tool:execute:safe"          # L0 tools (file_read, calendar_list, memory_search)
    TOOL_EXECUTE_MODERATE = "tool:execute:moderate"  # L1 tools (web_search, web_fetch, memory_store)
    TOOL_EXECUTE_SENSITIVE = "tool:execute:sensitive"# L2 tools (python_execute, git_commit, file_write)
    TOOL_EXECUTE_CRITICAL = "tool:execute:critical"  # L3 tools (shell_execute, file_delete)

    # Memory & State
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"

    # Chat & Generation
    CHAT_INTERACT = "chat:interact"


ROLE_PERMISSIONS_MATRIX: dict[Role, set[Permission]] = {
    Role.ADMIN: set(Permission),  # All permissions
    Role.OPERATOR: {
        Permission.SYSTEM_READ,
        Permission.AUDIT_READ,
        Permission.AUDIT_EXPORT,
        Permission.AGENT_READ,
        Permission.AGENT_ACTIVATE,
        Permission.AGENT_EXECUTE,
        Permission.TOOL_EXECUTE_SAFE,
        Permission.TOOL_EXECUTE_MODERATE,
        Permission.TOOL_EXECUTE_SENSITIVE,
        Permission.MEMORY_READ,
        Permission.MEMORY_WRITE,
        Permission.CHAT_INTERACT,
    },
    Role.AGENT: {
        Permission.AGENT_READ,
        Permission.TOOL_EXECUTE_SAFE,
        Permission.TOOL_EXECUTE_MODERATE,
        Permission.MEMORY_READ,
        Permission.CHAT_INTERACT,
    },
    Role.AUDITOR: {
        Permission.SYSTEM_READ,
        Permission.AUDIT_READ,
        Permission.AUDIT_EXPORT,
        Permission.AGENT_READ,
        Permission.MEMORY_READ,
    },
    Role.READ_ONLY: {
        Permission.SYSTEM_READ,
        Permission.AGENT_READ,
        Permission.MEMORY_READ,
    },
}


@dataclass
class ABACContext:
    """Dynamic environmental attributes evaluated during access authorization."""

    network_mode: NetworkMode = field(
        default_factory=lambda: getattr(settings, "NETWORK_MODE", NetworkMode.USER_AUTHORIZED_EGRESS)
    )
    is_loopback: bool = True
    session_id: str | None = None
    target_resource_owner: str | None = None
    operator_confirmed: bool = False
    requested_action_risk: float = 0.0


class AccessController:
    """Evaluates whether an authenticated Principal is authorized to perform an action."""

    def is_authorized(
        self,
        principal: Principal,
        required_permission: Permission,
        context: ABACContext | None = None,
    ) -> tuple[bool, str | None]:
        """Evaluates RBAC matrix followed by ABAC contextual constraints."""
        if context is None:
            context = ABACContext()

        # Wildcard scope super-admin grant
        if "*" in principal.scopes:
            return True, None

        # 1. RBAC Evaluation
        try:
            role_enum = Role(principal.role.lower())
        except ValueError:
            return False, f"Unknown role '{principal.role}'."

        granted_permissions = ROLE_PERMISSIONS_MATRIX.get(role_enum, set())
        if required_permission not in granted_permissions and required_permission.value not in principal.scopes:
            return False, f"Role '{principal.role}' lacks required permission '{required_permission.value}'."

        # 2. ABAC Evaluation
        # Constraint A: Audit destruction requires admin role AND explicit operator confirmation
        if required_permission == Permission.AUDIT_DELETE:
            if role_enum != Role.ADMIN or not context.operator_confirmed:
                return False, "Audit log purge requires ADMIN role with explicit operator confirmation."

        # Constraint B: In OFFLINE_AIRGAP mode, moderate/external network operations are blocked
        if context.network_mode == NetworkMode.OFFLINE_AIRGAP:
            if required_permission in {Permission.TOOL_EXECUTE_MODERATE}:
                return False, "Moderate tool execution restricted under OFFLINE_AIRGAP policy."

        # Constraint C: Critical tool execution (shell_execute) requires operator confirmation
        if required_permission == Permission.TOOL_EXECUTE_CRITICAL:
            if not context.operator_confirmed and role_enum != Role.ADMIN:
                return False, "Critical tool execution requires explicit operator confirmation."

        return True, None


access_controller = AccessController()
