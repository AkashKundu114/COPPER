"""Tool-Level Zero-Trust Permission Enforcement Policy.

Validates that any tool execution request is explicitly authorized for the
calling principal or agent, verifying least-privilege capability boundaries.
"""

from __future__ import annotations

from typing import Any

from app.ai.tools.registry import BaseTool
from app.core.guardian import DisagreementLevel, guardian_engine
from app.core.logger import logger
from app.core.security.access_control import Permission, access_controller
from app.core.security.agent_token import agent_token_service
from app.core.security.auth import Principal, PrincipalType


def get_required_tool_permission(guardian_level: int) -> Permission:
    if guardian_level <= 0:
        return Permission.TOOL_EXECUTE_SAFE
    elif guardian_level == 1:
        return Permission.TOOL_EXECUTE_MODERATE
    elif guardian_level == 2:
        return Permission.TOOL_EXECUTE_SENSITIVE
    return Permission.TOOL_EXECUTE_CRITICAL


class ToolAuthorizationPolicy:
    """Enforces zero-trust authorization at the ToolExecutor boundary."""

    def authorize_tool_call(
        self,
        tool: BaseTool,
        arguments: dict[str, Any],
        context: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """Verifies whether caller is authorized to invoke the specified tool."""
        agent_name = context.get("agent")
        agent_token_str = context.get("agent_token")
        principal: Principal | None = context.get("principal")

        # 1. If an AgentToken is provided, verify cryptographic validity and scope
        if agent_token_str:
            token_payload = agent_token_service.verify_token(agent_token_str)
            if not token_payload:
                return False, "AgentToken verification failed: invalid or expired token."

            if tool.name not in token_payload.allowed_tools:
                return (
                    False,
                    f"Tool authorization denied: Tool '{tool.name}' is outside granted capability scope for agent '{token_payload.agent_id}'.",
                )

        # 2. If called directly within agent context without an explicit token
        elif agent_name:
            # Check agent tool registry bindings
            from app.ai.tools.registry import tool_registry

            bound_tools = [t.name for t in tool_registry.get_tools_for_agent(agent_name)]
            if bound_tools and tool.name not in bound_tools:
                return (
                    False,
                    f"Agent authorization denied: Tool '{tool.name}' is not in authorized toolset for agent '{agent_name}'.",
                )

        # 3. If a Principal is provided (e.g. from API caller), evaluate RBAC
        if principal:
            req_perm = get_required_tool_permission(tool.guardian_level)
            is_auth, reason = access_controller.is_authorized(principal, req_perm)
            if not is_auth:
                return False, f"Principal '{principal.id}' unauthorized for tool '{tool.name}': {reason}"

        return True, None


tool_authorization_policy = ToolAuthorizationPolicy()
